"""
Registo dos models de Equipamentos no Django Admin (Passo 2).

A página de cada Equipamento mostra os seus certificados em linha (inline).
"""

from django.contrib import admin

from config.common import AuditoriaAdminMixin

from .models import Certificado, Equipamento


class CertificadoInline(admin.TabularInline):
    model = Certificado
    extra = 0


@admin.register(Equipamento)
class EquipamentoAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "numero_serie", "responsavel", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "numero_serie", "responsavel__nome")
    inlines = [CertificadoInline]


@admin.register(Certificado)
class CertificadoAdmin(AuditoriaAdminMixin, admin.ModelAdmin):
    list_display = ("equipamento", "tipo", "data_emissao", "data_validade")
    list_filter = ("tipo",)
    search_fields = ("equipamento__nome", "tipo")
    date_hierarchy = "data_validade"
