"""
Registo dos models de Funcionários no Django Admin.

A página de cada Funcionário mostra as suas despesas em linha (inline).
"""

from django.contrib import admin

from config.common import AuditoriaAdminMixin

from .models import DespesaFuncionario, Funcionario


class DespesaFuncionarioInline(admin.TabularInline):
    model = DespesaFuncionario
    extra = 0


@admin.register(Funcionario)
class FuncionarioAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "funcao", "nif", "ativo", "data_admissao")
    list_filter = ("ativo", "funcao")
    search_fields = ("nome", "nif", "email")
    inlines = [DespesaFuncionarioInline]


@admin.register(DespesaFuncionario)
class DespesaFuncionarioAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("funcionario", "descricao", "valor", "data")
    search_fields = ("funcionario__nome", "descricao")
    date_hierarchy = "data"
