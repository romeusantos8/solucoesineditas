"""
URLs da API de Clientes e Obras. O DefaultRouter gera as rotas CRUD.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    AlocacaoEquipamentoViewSet,
    AlocacaoFuncionarioViewSet,
    ClienteViewSet,
    ObraViewSet,
)

router = DefaultRouter()
router.register("clientes", ClienteViewSet)
router.register("obras", ObraViewSet)
router.register("alocacoes-funcionarios", AlocacaoFuncionarioViewSet)
router.register("alocacoes-equipamentos", AlocacaoEquipamentoViewSet)

urlpatterns = router.urls
