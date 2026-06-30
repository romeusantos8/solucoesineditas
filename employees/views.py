"""
Views de Funcionários (o "Controller"): CRUD completo via ModelViewSet.
"""

from rest_framework import viewsets

from config.common import AuditoriaViewSetMixin

from .models import DespesaFuncionario, Funcionario
from .serializers import DespesaFuncionarioSerializer, FuncionarioSerializer


class FuncionarioViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    filterset_fields = ["ativo", "funcao"]


class DespesaFuncionarioViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = DespesaFuncionario.objects.select_related("funcionario").all()
    serializer_class = DespesaFuncionarioSerializer
    filterset_fields = ["funcionario"]  # ?funcionario=ID
