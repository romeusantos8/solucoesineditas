"""
Views de Equipamentos (o "Controller"): CRUD completo via ModelViewSet.
"""

from rest_framework import viewsets

from .models import Certificado, Equipamento
from .serializers import CertificadoSerializer, EquipamentoSerializer


class EquipamentoViewSet(viewsets.ModelViewSet):
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    filterset_fields = ["ativo"]


class CertificadoViewSet(viewsets.ModelViewSet):
    queryset = Certificado.objects.select_related("equipamento").all()
    serializer_class = CertificadoSerializer
    filterset_fields = ["equipamento", "tipo"]  # ?equipamento=ID
