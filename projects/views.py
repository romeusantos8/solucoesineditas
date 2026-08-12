"""
Views de Clientes e Obras (o "Controller"): CRUD completo via ModelViewSet.
"""

from rest_framework import viewsets

from config.common import AuditoriaViewSetMixin

from .models import AlocacaoFuncionario, AutoObra, Cliente, Obra
from .serializers import (
    AlocacaoFuncionarioSerializer,
    AutoObraSerializer,
    ClienteSerializer,
    ObraSerializer,
)


class ClienteViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filterset_fields = ["ativo"]


class ObraViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    # prefetch: alocações + funcionários + equipamentos de cada funcionário
    # (para os equipamentos derivados serem calculados sem N+1 queries).
    queryset = (
        Obra.objects.select_related("cliente")
        .prefetch_related(
            "alocacaofuncionario_set__funcionario__equipamentos",
        )
        .all()
    )
    serializer_class = ObraSerializer
    filterset_fields = ["cliente", "estado"]


class AlocacaoFuncionarioViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = AlocacaoFuncionario.objects.select_related(
        "obra", "funcionario"
    ).all()
    serializer_class = AlocacaoFuncionarioSerializer
    filterset_fields = ["obra", "funcionario"]


class AutoObraViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = AutoObra.objects.select_related("obra").all()
    serializer_class = AutoObraSerializer
    # ?obra=ID (autos de uma obra), ?estado=, ?ano=
    filterset_fields = ["obra", "estado", "ano"]
