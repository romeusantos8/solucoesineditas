"""
URLs da API de Fichas Médicas. Acesso restrito (ver views).
"""

from rest_framework.routers import DefaultRouter

from .views import FichaMedicaViewSet

router = DefaultRouter()
router.register("fichas-medicas", FichaMedicaViewSet)

urlpatterns = router.urls
