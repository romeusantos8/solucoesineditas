"""
URLs da API de Equipamentos. O DefaultRouter gera as rotas CRUD de cada ViewSet.
"""

from rest_framework.routers import DefaultRouter

from .views import CertificadoViewSet, EquipamentoViewSet

router = DefaultRouter()
router.register("equipamentos", EquipamentoViewSet)
router.register("certificados", CertificadoViewSet)

urlpatterns = router.urls
