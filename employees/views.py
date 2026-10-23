"""
Views de Funcionários (o "Controller"): CRUD completo via ModelViewSet, a gestão
da conta do portal e o próprio portal de despesas do funcionário.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import AcessoFuncionario, funcionario_do_utilizador
from config.common import AuditoriaViewSetMixin

from .models import DespesaFuncionario, Funcionario
from .serializers import (
    AcessoFuncionarioSerializer,
    DespesaFuncionarioSerializer,
    FuncionarioSerializer,
    MinhaDespesaSerializer,
)

User = get_user_model()


class FuncionarioViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = Funcionario.objects.select_related("utilizador").all()
    serializer_class = FuncionarioSerializer
    filterset_fields = ["ativo", "funcao"]

    @extend_schema(request=AcessoFuncionarioSerializer, responses=FuncionarioSerializer)
    @action(detail=True, methods=["post", "delete"])
    def acesso(self, request, pk=None):
        """
        Conta do funcionário no portal de despesas.
        POST {username, password} → cria a conta, ou (se já existir) troca o
        username/palavra-passe e volta a ativá-la.
        DELETE → revoga: desativa o User mas mantém a ligação (um User solto
        seria tratado como utilizador de gestão).
        """
        funcionario = self.get_object()

        if request.method == "DELETE":
            if funcionario.utilizador is not None:
                funcionario.utilizador.is_active = False
                funcionario.utilizador.save(update_fields=["is_active"])
            return Response(self.get_serializer(funcionario).data)

        dados = AcessoFuncionarioSerializer(instance=funcionario, data=request.data)
        dados.is_valid(raise_exception=True)
        with transaction.atomic():
            utilizador = funcionario.utilizador or User(is_staff=False)
            utilizador.username = dados.validated_data["username"]
            utilizador.set_password(dados.validated_data["password"])
            utilizador.is_active = True
            utilizador.save()
            if funcionario.utilizador_id != utilizador.pk:
                funcionario.utilizador = utilizador
                funcionario.atualizado_por = request.user
                funcionario.save(update_fields=["utilizador", "atualizado_por", "atualizado_em"])
        return Response(self.get_serializer(funcionario).data, status=status.HTTP_200_OK)


class DespesaFuncionarioViewSet(AuditoriaViewSetMixin, viewsets.ModelViewSet):
    queryset = DespesaFuncionario.objects.select_related("funcionario").all()
    serializer_class = DespesaFuncionarioSerializer
    filterset_fields = ["funcionario"]  # ?funcionario=ID


@extend_schema(tags=["Portal do funcionário"])
class MinhasDespesasViewSet(
    AuditoriaViewSetMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Portal do funcionário: lista e regista as despesas do PRÓPRIO utilizador.
    Só listar e criar — corrigir ou apagar fica com a gestão.
    """

    serializer_class = MinhaDespesaSerializer
    permission_classes = [AcessoFuncionario]
    # O queryset de classe só serve ao router/esquema; o real é filtrado.
    queryset = DespesaFuncionario.objects.none()

    def get_queryset(self):
        funcionario = funcionario_do_utilizador(self.request.user)
        return DespesaFuncionario.objects.filter(funcionario=funcionario)

    def perform_create(self, serializer):
        serializer.save(
            funcionario=funcionario_do_utilizador(self.request.user),
            criado_por=self.request.user,
            atualizado_por=self.request.user,
        )
