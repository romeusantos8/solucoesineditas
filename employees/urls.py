"""
URLs da API de Funcionários. O DefaultRouter gera as rotas CRUD de cada ViewSet.
"""

from rest_framework.routers import DefaultRouter

from .views import DespesaFuncionarioViewSet, FuncionarioViewSet, MinhasDespesasViewSet

router = DefaultRouter()
router.register("funcionarios", FuncionarioViewSet)
router.register("despesas-funcionarios", DespesaFuncionarioViewSet)
# Portal do funcionário (só as despesas do próprio utilizador).
router.register("minhas-despesas", MinhasDespesasViewSet, basename="minhas-despesas")

urlpatterns = router.urls
