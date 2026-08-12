"""
URLs da API de Clientes e Obras. O DefaultRouter gera as rotas CRUD.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    AlocacaoFuncionarioViewSet,
    AutoObraViewSet,
    ClienteViewSet,
    ObraViewSet,
)

router = DefaultRouter()
router.register("clientes", ClienteViewSet)
router.register("obras", ObraViewSet)
router.register("alocacoes-funcionarios", AlocacaoFuncionarioViewSet)
router.register("autos-obras", AutoObraViewSet)

urlpatterns = router.urls
