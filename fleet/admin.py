"""
Registo dos models da Frota no Django Admin (Passo 2).

A página de cada Viatura mostra os seus seguros, inspeções e despesas em linha
(inlines), para gerir tudo num só sítio.
"""

from django.contrib import admin

from config.common import AuditoriaAdminMixin

from .models import DespesaViatura, Inspecao, SeguroViatura, Viatura


class SeguroViaturaInline(admin.TabularInline):
    model = SeguroViatura
    extra = 0


class InspecaoInline(admin.TabularInline):
    model = Inspecao
    extra = 0


class DespesaViaturaInline(admin.TabularInline):
    model = DespesaViatura
    extra = 0


@admin.register(Viatura)
class ViaturaAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("matricula", "marca", "modelo", "ano", "responsavel", "ativa")
    list_filter = ("ativa", "marca")
    search_fields = ("matricula", "marca", "modelo")
    inlines = [SeguroViaturaInline, InspecaoInline, DespesaViaturaInline]


@admin.register(SeguroViatura)
class SeguroViaturaAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("viatura", "seguradora", "apolice", "valor", "data_validade")
    list_filter = ("seguradora",)
    search_fields = ("viatura__matricula", "seguradora", "apolice")
    date_hierarchy = "data_validade"


@admin.register(Inspecao)
class InspecaoAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("viatura", "data_inspecao", "data_validade", "resultado")
    list_filter = ("resultado",)
    search_fields = ("viatura__matricula",)
    date_hierarchy = "data_validade"


@admin.register(DespesaViatura)
class DespesaViaturaAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("viatura", "descricao", "valor", "data")
    search_fields = ("viatura__matricula", "descricao")
    date_hierarchy = "data"
