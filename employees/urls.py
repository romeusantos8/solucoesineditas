"""
URLs da API de Funcionários. O DefaultRouter gera as rotas CRUD de cada ViewSet.
"""

from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import (
    DespesaFuncionarioViewSet,
    FuncionarioViewSet,
    MinhasDespesasViewSet,
    confirmar_pagamento,
)

router = DefaultRouter()
router.register("funcionarios", FuncionarioViewSet)
router.register("despesas-funcionarios", DespesaFuncionarioViewSet)
# Portal do funcionário (só as despesas do próprio utilizador).
router.register("minhas-despesas", MinhasDespesasViewSet, basename="minhas-despesas")

urlpatterns = [
    # Link do email enviado à empresa (público; autorizado pelo token assinado).
    path("confirmar-pagamento/<str:token>/", confirmar_pagamento, name="confirmar-pagamento"),
    *router.urls,
]
