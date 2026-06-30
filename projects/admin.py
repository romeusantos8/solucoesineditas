"""
Registo dos models de Clientes e Obras no Django Admin.

A página de cada Obra mostra as alocações de funcionários e equipamentos em
linha (inlines), para as gerir num só sítio.
"""

from django.contrib import admin

from config.common import AuditoriaAdminMixin

from .models import (
    AlocacaoEquipamento,
    AlocacaoFuncionario,
    Cliente,
    Obra,
)


class AlocacaoFuncionarioInline(admin.TabularInline):
    model = AlocacaoFuncionario
    extra = 0


class AlocacaoEquipamentoInline(admin.TabularInline):
    model = AlocacaoEquipamento
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "nif", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "nif", "email")


@admin.register(Obra)
class ObraAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "cliente", "estado", "data_inicio", "data_fim_prevista")
    list_filter = ("estado",)
    search_fields = ("nome", "cliente__nome")
    date_hierarchy = "data_inicio"
    inlines = [AlocacaoFuncionarioInline, AlocacaoEquipamentoInline]


@admin.register(AlocacaoFuncionario)
class AlocacaoFuncionarioAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("funcionario", "obra", "data_inicio", "data_fim")
    search_fields = ("funcionario__nome", "obra__nome")


@admin.register(AlocacaoEquipamento)
class AlocacaoEquipamentoAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("equipamento", "obra", "data_inicio", "data_fim")
    search_fields = ("equipamento__nome", "obra__nome")
