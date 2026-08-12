"""
Views da app de Relatórios (o "Controller").

Só LÊ as outras apps (como a app `alerts`): importa os models de despesas mas
nunca os altera. Não tem models nem migrações próprias.

GET /api/reports/despesas-mensais/?tipo=&entidade=&ano=&mes=
  - tipo:     "funcionario" | "viatura" (obrigatório)
  - entidade: id do funcionário/viatura (obrigatório)
  - ano:      YYYY (default: ano atual)
  - mes:      1-12 (opcional) — se presente, junta o detalhe (lista) desse mês
Devolve os 12 totais mensais do ano; com `mes`, também as despesas desse mês.
"""

from datetime import date
from decimal import Decimal

from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from employees.models import DespesaFuncionario, Funcionario
from equipment.models import Equipamento
from fleet.models import DespesaViatura
from projects.models import AutoObra, Obra

# Config por tipo: model e nome do campo FK correspondente.
_FONTES = {
    "funcionario": {"model": DespesaFuncionario, "fk": "funcionario_id"},
    "viatura": {"model": DespesaViatura, "fk": "viatura_id"},
}


def _inteiro(request, nome, default=None):
    bruto = request.query_params.get(nome, default)
    if bruto is None or bruto == "":
        raise ValidationError({nome: "Obrigatório."})
    try:
        return int(bruto)
    except (TypeError, ValueError):
        raise ValidationError({nome: "Tem de ser um número inteiro."})


class DespesasMensaisView(APIView):
    """Total de despesas por mês de um funcionário ou viatura, num ano."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tipo = request.query_params.get("tipo")
        if tipo not in _FONTES:
            raise ValidationError(
                {"tipo": "Tem de ser 'funcionario' ou 'viatura'."}
            )
        entidade = _inteiro(request, "entidade")
        ano = _inteiro(request, "ano", default=date.today().year)

        fonte = _FONTES[tipo]
        base = fonte["model"].objects.filter(
            **{fonte["fk"]: entidade}, data__year=ano
        )

        # Soma por mês (1 query).
        somas = (
            base.values("data__month")
            .annotate(total=Sum("valor"))
            .order_by("data__month")
        )
        por_mes = {linha["data__month"]: linha["total"] for linha in somas}

        # Devolve sempre os 12 meses (0.00 nos que não têm despesas).
        meses = [
            {"mes": m, "total": str(por_mes.get(m, Decimal("0.00")))}
            for m in range(1, 13)
        ]

        resposta = {
            "tipo": tipo,
            "entidade": entidade,
            "ano": ano,
            "total_ano": str(base.aggregate(t=Sum("valor"))["t"] or Decimal("0.00")),
            "meses": meses,
        }

        # Detalhe opcional de um mês (?mes=N).
        mes_bruto = request.query_params.get("mes")
        if mes_bruto not in (None, ""):
            mes = _inteiro(request, "mes")
            if not 1 <= mes <= 12:
                raise ValidationError({"mes": "Tem de estar entre 1 e 12."})
            detalhe = base.filter(data__month=mes).order_by("data")
            resposta["mes"] = mes
            resposta["detalhe"] = [
                {
                    "id": d.id,
                    "descricao": d.descricao,
                    "valor": str(d.valor),
                    "data": d.data.isoformat(),
                }
                for d in detalhe
            ]

        return Response(resposta)


class FaturacaoObraView(APIView):
    """
    Total faturado numa obra + lista dos seus autos mensais.

    GET /api/reports/faturacao-obra/?obra=ID
      - obra: id da obra (obrigatório)
    Devolve o total de todos os autos, o total só dos já faturados, e a lista
    de autos (mais recentes primeiro).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        obra_id = _inteiro(request, "obra")
        try:
            obra = Obra.objects.get(pk=obra_id)
        except Obra.DoesNotExist:
            raise ValidationError({"obra": "Obra não encontrada."})

        autos = obra.autos.all()  # já ordenados por -ano, -mes (Meta.ordering)

        total = autos.aggregate(t=Sum("valor"))["t"] or Decimal("0.00")
        total_faturado = (
            autos.filter(estado=AutoObra.Estado.FATURADO).aggregate(
                t=Sum("valor")
            )["t"]
            or Decimal("0.00")
        )

        return Response({
            "obra": obra.id,
            "obra_nome": obra.nome,
            "total": str(total),
            "total_faturado": str(total_faturado),
            "total_por_faturar": str(total - total_faturado),
            "autos": [
                {
                    "id": a.id,
                    "ano": a.ano,
                    "mes": a.mes,
                    "valor": str(a.valor),
                    "descricao": a.descricao,
                    "estado": a.estado,
                    "estado_display": a.get_estado_display(),
                }
                for a in autos
            ],
        })


class EquipamentosFuncionarioView(APIView):
    """
    Equipamentos à responsabilidade de um funcionário.

    GET /api/reports/equipamentos-funcionario/?funcionario=ID
      - funcionario: id do funcionário (obrigatório)
    Devolve a lista de equipamentos de que esse funcionário é responsável.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        funcionario_id = _inteiro(request, "funcionario")
        try:
            funcionario = Funcionario.objects.get(pk=funcionario_id)
        except Funcionario.DoesNotExist:
            raise ValidationError({"funcionario": "Funcionário não encontrado."})

        equipamentos = Equipamento.objects.filter(
            responsavel_id=funcionario_id
        ).order_by("nome")

        return Response({
            "funcionario": funcionario.id,
            "funcionario_nome": funcionario.nome,
            "total": equipamentos.count(),
            "equipamentos": [
                {
                    "id": e.id,
                    "nome": e.nome,
                    "numero_serie": e.numero_serie,
                    "ativo": e.ativo,
                }
                for e in equipamentos
            ],
        })
