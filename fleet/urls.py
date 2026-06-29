"""
URLs da API da Frota.

O DefaultRouter gera automaticamente todas as rotas CRUD para cada ViewSet
registado (ex.: /viaturas/, /viaturas/{id}/, ...).
"""

from rest_framework.routers import DefaultRouter

from .views import (
    DespesaViaturaViewSet,
    InspecaoViewSet,
    SeguroViaturaViewSet,
    ViaturaViewSet,
)

router = DefaultRouter()
router.register("viaturas", ViaturaViewSet)
router.register("seguros", SeguroViaturaViewSet)
router.register("inspecoes", InspecaoViewSet)
router.register("despesas", DespesaViaturaViewSet)

urlpatterns = router.urls
