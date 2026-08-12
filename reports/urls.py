"""
URLs da app de Relatórios. Não são ViewSets (agregam várias fontes), por isso
rotas simples, sem router.
"""

from django.urls import path

from .views import (
    DespesasMensaisView,
    EquipamentosFuncionarioView,
    FaturacaoObraView,
)

urlpatterns = [
    path(
        "reports/despesas-mensais/",
        DespesasMensaisView.as_view(),
        name="reports-despesas-mensais",
    ),
    path(
        "reports/faturacao-obra/",
        FaturacaoObraView.as_view(),
        name="reports-faturacao-obra",
    ),
    path(
        "reports/equipamentos-funcionario/",
        EquipamentosFuncionarioView.as_view(),
        name="reports-equipamentos-funcionario",
    ),
]
