"""
Registo da Ficha Médica no Admin. Dados de saúde (RGPD) — o Admin já restringe
o acesso a utilizadores staff com a permissão do model.
"""

from django.contrib import admin

from config.common import AuditoriaAdminMixin

from .models import FichaMedica


@admin.register(FichaMedica)
class FichaMedicaAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("funcionario", "aptidao", "data_exame", "data_validade")
    list_filter = ("aptidao",)
    search_fields = ("funcionario__nome",)
    date_hierarchy = "data_validade"
