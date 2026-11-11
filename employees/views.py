"""
Views de Funcionários (o "Controller"): CRUD completo via ModelViewSet, a gestão
da conta do portal e o próprio portal de despesas do funcionário.
"""

from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from accounts.permissions import AcessoFuncionario, funcionario_do_utilizador
from config.common import AuditoriaViewSetMixin

from .models import DespesaFuncionario, Funcionario
from .notificacoes import despesa_do_token, notificar_nova_despesa
from .serializers import (
    AcessoFuncionarioSerializer,
    DespesaFuncionarioSerializer,
    FuncionarioSerializer,
    MinhaDespesaSerializer,
)

User = get_user_model()


class PaginacaoDespesas(PageNumberPagination):
    """Listas de despesas mais curtas que o PAGE_SIZE global (50)."""

    page_size = 10


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
        # Uma conta de staff ligada a um funcionário é de gestão: não se mexe
        # por aqui (senão um gestor comum tomava-lhe a conta).
        if funcionario.utilizador is not None and funcionario.utilizador.is_staff:
            raise PermissionDenied("Esta conta é de gestão e não se gere pelo portal.")

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
    # Desempate por id: com várias despesas no mesmo dia, a paginação fica estável.
    queryset = DespesaFuncionario.objects.select_related("funcionario").order_by("-data", "-id")
    serializer_class = DespesaFuncionarioSerializer
    pagination_class = PaginacaoDespesas
    filterset_fields = ["funcionario", "paga"]  # ?funcionario=ID&paga=false


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
    pagination_class = PaginacaoDespesas
    permission_classes = [AcessoFuncionario]
    # Nome do limite em DEFAULT_THROTTLE_RATES (settings).
    throttle_scope = "despesas_portal"
    # O queryset de classe só serve ao router/esquema; o real é filtrado.
    queryset = DespesaFuncionario.objects.none()

    def get_throttles(self):
        # Só registar é limitado (cada registo envia um email); listar não. O
        # contador é por utilizador e, ao exceder, o DRF responde 429.
        if self.action == "create":
            return [ScopedRateThrottle()]
        return []

    def get_queryset(self):
        funcionario = funcionario_do_utilizador(self.request.user)
        return DespesaFuncionario.objects.filter(funcionario=funcionario).order_by("-data", "-id")

    def perform_create(self, serializer):
        despesa = serializer.save(
            funcionario=funcionario_do_utilizador(self.request.user),
            criado_por=self.request.user,
            atualizado_por=self.request.user,
        )
        notificar_nova_despesa(despesa, self.request)


@csrf_exempt  # quem autoriza é o token assinado do link, não uma sessão
@never_cache
@require_http_methods(["GET", "POST"])
def confirmar_pagamento(request, token):
    """
    Página aberta a partir do link do email. O GET só mostra a despesa: os filtros
    de email abrem os links sozinhos, e um GET que alterasse dados marcaria
    despesas como pagas sem ninguém clicar. Quem paga é o POST do botão.
    """
    try:
        despesa = DespesaFuncionario.objects.select_related("funcionario").get(
            pk=despesa_do_token(token)
        )
    except (signing.BadSignature, DespesaFuncionario.DoesNotExist):
        return render(request, "employees/confirmar_pagamento.html", status=404)

    if request.method == "POST" and not despesa.paga:
        despesa.paga = True
        # Sem sessão não se sabe quem clicou: não fica o nome do último a editar.
        despesa.atualizado_por = None
        despesa.save(update_fields=["paga", "atualizado_por", "atualizado_em"])
    return render(request, "employees/confirmar_pagamento.html", {"despesa": despesa})
