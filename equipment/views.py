"""
Views de Equipamentos (o "Controller"): CRUD completo via ModelViewSet.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from config.common import AuditoriaViewSetMixin

from .models import Certificado, Equipamento
from .serializers import CertificadoSerializer, EquipamentoSerializer


@extend_schema(tags=["Equipamentos"])
class EquipamentoViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Equipamento.objects.all()
    serializer_class = EquipamentoSerializer
    filterset_fields = ["ativo"]


@extend_schema(tags=["Equipamentos"])
class CertificadoViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Certificado.objects.select_related("equipamento").all()
    serializer_class = CertificadoSerializer
    filterset_fields = ["equipamento", "tipo"]  # ?equipamento=ID
