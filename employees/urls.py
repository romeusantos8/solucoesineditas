"""
URLs da API de Funcionários. O DefaultRouter gera as rotas CRUD de cada ViewSet.
"""

from rest_framework.routers import DefaultRouter

from .views import DespesaFuncionarioViewSet, FuncionarioViewSet

router = DefaultRouter()
router.register("funcionarios", FuncionarioViewSet)
router.register("despesas-funcionarios", DespesaFuncionarioViewSet)

urlpatterns = router.urls
