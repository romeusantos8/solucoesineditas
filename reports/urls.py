"""
URLs da app de Relatórios. Não são ViewSets (agregam várias fontes), por isso
rotas simples, sem router.
"""

from django.urls import path

from .views import DespesasMensaisView

urlpatterns = [
    path(
        "reports/despesas-mensais/",
        DespesasMensaisView.as_view(),
        name="reports-despesas-mensais",
    ),
]
