"""
URL do dashboard de alertas: GET /api/alerts/.

Não é um ViewSet (junta várias fontes), por isso é uma rota simples, sem router.
"""

from django.urls import path

from .views import AlertasView

urlpatterns = [
    path("alerts/", AlertasView.as_view(), name="alerts"),
]
