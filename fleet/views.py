"""
Views da Frota (MVC: o "Controller" — a lógica que responde aos pedidos).

Usamos ModelViewSet: numa só classe ganhamos list/create/retrieve/update/
destroy (CRUD completo) ligados ao router em urls.py.
"""

from rest_framework import viewsets

from .models import DespesaViatura, Inspecao, SeguroViatura, Viatura
from .serializers import (
    DespesaViaturaSerializer,
    InspecaoSerializer,
    SeguroViaturaSerializer,
    ViaturaSerializer,
)


class ViaturaViewSet(viewsets.ModelViewSet):
    queryset = Viatura.objects.all()
    serializer_class = ViaturaSerializer
    filterset_fields = ["ativa", "marca"]


class SeguroViaturaViewSet(viewsets.ModelViewSet):
    # select_related evita uma query extra por linha ao aceder à viatura.
    queryset = SeguroViatura.objects.select_related("viatura").all()
    serializer_class = SeguroViaturaSerializer
    filterset_fields = ["viatura"]  # ?viatura=ID


class InspecaoViewSet(viewsets.ModelViewSet):
    queryset = Inspecao.objects.select_related("viatura").all()
    serializer_class = InspecaoSerializer
    filterset_fields = ["viatura", "resultado"]


class DespesaViaturaViewSet(viewsets.ModelViewSet):
    queryset = DespesaViatura.objects.select_related("viatura").all()
    serializer_class = DespesaViaturaSerializer
    filterset_fields = ["viatura"]
