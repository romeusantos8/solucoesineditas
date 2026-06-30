"""
Views da Ficha Médica (o "Controller").

ACESSO RESTRITO: dados de saúde (RGPD). Ao contrário do resto da API (que basta
estar autenticado), aqui exige-se IsAdminUser (is_staff=True). É a medida de
acesso mínima desta fase; um sistema de permissões por perfil mais fino fica
para a fase de roles.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from config.common import AuditoriaViewSetMixin

from .models import FichaMedica
from .serializers import FichaMedicaSerializer


class FichaMedicaViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = FichaMedica.objects.select_related("funcionario").all()
    serializer_class = FichaMedicaSerializer
    # Acesso só a staff/admin — sobrepõe o IsAuthenticated global.
    permission_classes = [IsAdminUser]
    filterset_fields = ["funcionario", "aptidao"]
