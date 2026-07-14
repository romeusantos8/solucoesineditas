"""
Registo dos models de Clientes e Obras no Django Admin.

A página de cada Obra mostra as alocações de funcionários em linha (inline).
Os equipamentos de uma obra são derivados dos funcionários alocados (ver
serializers) — não há alocação direta de equipamento à obra.
"""

from django.contrib import admin

from config.common import AuditoriaAdminMixin

from .models import AlocacaoFuncionario, Cliente, Obra


class AlocacaoFuncionarioInline(admin.TabularInline):
    model = AlocacaoFuncionario
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
    inlines = [AlocacaoFuncionarioInline]


@admin.register(AlocacaoFuncionario)
class AlocacaoFuncionarioAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("funcionario", "obra", "data_inicio", "data_fim")
    search_fields = ("funcionario__nome", "obra__nome")
