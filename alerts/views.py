"""
View da app de Alertas (MVC: o "Controller").

GET /api/alerts/?dias=N&expirados_desde=M  → lista unificada de prazos a expirar
(e expirados recentes), ordenada do mais urgente para o menos urgente. Junta
seguros, inspeções, certificados e fichas médicas. Esta app só LÊ as outras
(regra do README): importa os models mas nunca os altera.

Só entram prazos que ainda precisam de atenção:
- não renovados: um registo com sucessor (outro registo do mesmo recurso com
  validade posterior) já foi tratado e sai do dashboard;
- de recursos ativos: viaturas abatidas, equipamentos inativos e funcionários
  que saíram não geram alertas.

Parâmetros:
- dias (default 60): janela futura — inclui o que expira até hoje+dias.
- expirados_desde (default 90): fundo da janela — inclui expirados só dos
  últimos M dias, para o histórico antigo não se acumular para sempre na
  resposta. expirados_desde=0 mostra apenas o que ainda não expirou.

A resposta é paginada (como os restantes endpoints).
"""

from datetime import date, timedelta

from django.db.models import Exists, OuterRef
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from equipment.models import Certificado
from fleet.models import Inspecao, SeguroViatura
from health_records.models import FichaMedica

from .serializers import AlertaSerializer

# Defaults da janela. DIAS = quão longe no futuro olhamos; EXPIRADOS_DESDE =
# quão atrás no passado ainda mostramos os já vencidos.
DIAS_DEFAULT = 60
EXPIRADOS_DESDE_DEFAULT = 90
# Máximo das duas janelas (10 anos). Sem teto, um valor absurdo empurrava a data
# para lá do ano 9999 e o pedido rebentava (erro 500 em vez de 400).
JANELA_MAXIMA = 3650


def _parse_inteiro_nao_negativo(request, nome, default):
    """Lê e valida um parâmetro inteiro entre 0 e JANELA_MAXIMA da querystring."""
    bruto = request.query_params.get(nome, default)
    try:
        valor = int(bruto)
    except (TypeError, ValueError):
        raise ValidationError({nome: "Tem de ser um número inteiro."})
    if valor < 0:
        raise ValidationError({nome: "Tem de ser um número positivo."})
    if valor > JANELA_MAXIMA:
        raise ValidationError({nome: f"Não pode ser superior a {JANELA_MAXIMA}."})
    return valor


def _nao_renovados(queryset, **mesmo_recurso):
    """
    Exclui os registos já renovados: os que têm, para o mesmo recurso, outro
    registo com validade posterior. `mesmo_recurso` diz o que conta como "o
    mesmo prazo" (ex.: viatura=OuterRef("viatura")).
    """
    sucessor = queryset.model.objects.filter(
        data_validade__gt=OuterRef("data_validade"), **mesmo_recurso
    )
    return queryset.exclude(Exists(sucessor))


def _alerta(registo, tipo, recurso, recurso_id):
    """Converte um registo com validade no dicionário comum de alerta."""
    return {
        "tipo": tipo,
        "descricao": str(registo),
        "data_validade": registo.data_validade,
        "dias_para_expirar": registo.dias_para_expirar,
        "expirado": registo.expirado,
        "recurso": recurso,
        "recurso_id": recurso_id,
        "registo_id": registo.id,
    }


@extend_schema(
    tags=["Alertas"],
    parameters=[
        OpenApiParameter(
            "dias",
            OpenApiTypes.INT,
            description="Janela futura em dias (0–3650, default 60).",
        ),
        OpenApiParameter(
            "expirados_desde",
            OpenApiTypes.INT,
            description="Quantos dias atrás ainda mostrar expirados (0–3650, default 90).",
        ),
    ],
    responses=AlertaSerializer(many=True),
)
class AlertasView(APIView):
    """Dashboard de prazos. Só leitura; exige autenticação (default do projeto)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        dias = _parse_inteiro_nao_negativo(request, "dias", DIAS_DEFAULT)
        expirados_desde = _parse_inteiro_nao_negativo(
            request, "expirados_desde", EXPIRADOS_DESDE_DEFAULT
        )

        hoje = date.today()
        # Janela fechada nas duas pontas: do passado recente (piso) ao futuro
        # próximo (teto). Sem o piso, o histórico de expirados crescia sem fim.
        piso = hoje - timedelta(days=expirados_desde)
        teto = hoje + timedelta(days=dias)

        alertas = []
        na_janela = {"data_validade__range": (piso, teto)}

        seguros = _nao_renovados(
            SeguroViatura.objects.select_related("viatura").filter(
                viatura__ativa=True, **na_janela
            ),
            viatura=OuterRef("viatura"),
        )
        for s in seguros:
            alertas.append(_alerta(s, "seguro", "viatura", s.viatura_id))

        inspecoes = _nao_renovados(
            Inspecao.objects.select_related("viatura").filter(
                viatura__ativa=True, **na_janela
            ),
            viatura=OuterRef("viatura"),
        )
        for i in inspecoes:
            alertas.append(_alerta(i, "inspecao", "viatura", i.viatura_id))

        # Um equipamento pode ter vários tipos de certificado: só um do mesmo
        # tipo o renova. O tipo é texto livre, por isso compara sem maiúsculas.
        certificados = _nao_renovados(
            Certificado.objects.select_related("equipamento").filter(
                equipamento__ativo=True, **na_janela
            ),
            equipamento=OuterRef("equipamento"),
            tipo__iexact=OuterRef("tipo"),
        )
        for c in certificados:
            alertas.append(_alerta(c, "certificado", "equipamento", c.equipamento_id))

        # Fichas médicas: a descrição (do __str__) só identifica o funcionário,
        # não revela dados clínicos — adequado para um alerta de prazo aqui.
        # São OneToOne (uma por funcionário), por isso não há renovações a
        # excluir: renovar é editar a ficha (Admin) ou substituí-la (app).
        fichas = FichaMedica.objects.select_related("funcionario").filter(
            funcionario__ativo=True, **na_janela
        )
        for f in fichas:
            alertas.append(_alerta(f, "ficha_medica", "funcionario", f.funcionario_id))

        # Mais urgente primeiro: menos dias para expirar (negativos = já expirados
        # ficam no topo).
        alertas.sort(key=lambda a: a["dias_para_expirar"])

        # Pagina a lista combinada (usa o PAGE_SIZE global do DRF). A APIView não
        # pagina sozinha, por isso instanciamos o paginador à mão.
        paginator = PageNumberPagination()
        pagina = paginator.paginate_queryset(alertas, request, view=self)
        serializer = AlertaSerializer(pagina, many=True)
        return paginator.get_paginated_response(serializer.data)
