"""
View da app de Alertas (MVC: o "Controller").

GET /api/alerts/?dias=N  → lista unificada de prazos a expirar (e já expirados),
ordenada do mais urgente para o menos urgente. Junta seguros, inspeções e
certificados. Esta app só LÊ as outras (regra do README): importa os models de
fleet/equipment mas nunca os altera.
"""

from datetime import date, timedelta

from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from equipment.models import Certificado
from fleet.models import Inspecao, SeguroViatura

from .serializers import AlertaSerializer

# Janela por defeito (a maior referida no README). O cliente pode pedir outra.
DIAS_DEFAULT = 60


def _parse_dias(request):
    """Lê e valida o parâmetro ?dias=N (inteiro positivo)."""
    bruto = request.query_params.get("dias", DIAS_DEFAULT)
    try:
        dias = int(bruto)
    except (TypeError, ValueError):
        raise ValidationError({"dias": "Tem de ser um número inteiro."})
    if dias < 0:
        raise ValidationError({"dias": "Tem de ser um número positivo."})
    return dias


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


class AlertasView(APIView):
    """Dashboard de prazos. Só leitura; exige autenticação (default do projeto)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        dias = _parse_dias(request)
        # Limite superior da janela: tudo o que expira até hoje+dias (inclusive).
        # Sem limite inferior de propósito: itens já expirados (validade < hoje)
        # entram também, como os alertas mais urgentes.
        limite = date.today() + timedelta(days=dias)

        alertas = []

        seguros = SeguroViatura.objects.select_related("viatura").filter(
            data_validade__lte=limite
        )
        for s in seguros:
            alertas.append(_alerta(s, "seguro", "viatura", s.viatura_id))

        inspecoes = Inspecao.objects.select_related("viatura").filter(
            data_validade__lte=limite
        )
        for i in inspecoes:
            alertas.append(_alerta(i, "inspecao", "viatura", i.viatura_id))

        certificados = Certificado.objects.select_related("equipamento").filter(
            data_validade__lte=limite
        )
        for c in certificados:
            alertas.append(_alerta(c, "certificado", "equipamento", c.equipamento_id))

        # Mais urgente primeiro: menos dias para expirar (negativos = já expirados
        # ficam no topo).
        alertas.sort(key=lambda a: a["dias_para_expirar"])

        serializer = AlertaSerializer(alertas, many=True)
        return Response(serializer.data)
