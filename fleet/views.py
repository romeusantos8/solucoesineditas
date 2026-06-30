"""
Views da Frota (MVC: o "Controller" — a lógica que responde aos pedidos).

Usamos ModelViewSet: numa só classe ganhamos list/create/retrieve/update/
destroy (CRUD completo) ligados ao router em urls.py.
"""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets

from config.common import AuditoriaViewSetMixin

from .models import DespesaViatura, Inspecao, SeguroViatura, Viatura
from .serializers import (
    DespesaViaturaSerializer,
    InspecaoSerializer,
    SeguroViaturaSerializer,
    ViaturaSerializer,
)

# Agrupa todos os endpoints desta app sob a mesma secção "Frota" no Swagger.
# (Sem isto, o drf-spectacular usaria o 1º segmento do URL — "api" — para todos.)


@extend_schema(tags=["Frota"])
class ViaturaViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Viatura.objects.all()
    serializer_class = ViaturaSerializer
    filterset_fields = ["ativa", "marca"]


@extend_schema(tags=["Frota"])
class SeguroViaturaViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    # select_related evita uma query extra por linha ao aceder à viatura.
    queryset = SeguroViatura.objects.select_related("viatura").all()
    serializer_class = SeguroViaturaSerializer
    filterset_fields = ["viatura"]  # ?viatura=ID


@extend_schema(tags=["Frota"])
class InspecaoViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Inspecao.objects.select_related("viatura").all()
    serializer_class = InspecaoSerializer
    filterset_fields = ["viatura", "resultado"]


@extend_schema(tags=["Frota"])
class DespesaViaturaViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = DespesaViatura.objects.select_related("viatura").all()
    serializer_class = DespesaViaturaSerializer
    filterset_fields = ["viatura"]
