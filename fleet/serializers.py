"""
Serializers da Frota (numa API, o "template"/View é o JSON que estes produzem).

Um serializer faz duas coisas: valida os dados que entram (POST/PUT) e converte
os objetos do model em JSON na saída. As validações de negócio que falaste
adicionar mais tarde vivem aqui (métodos validate_<campo> / validate).
"""

from rest_framework import serializers

from config.common import ModelCleanSerializerMixin

from .models import DespesaViatura, Inspecao, SeguroViatura, Viatura


class ViaturaSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Viatura
        fields = [
            "id",
            "matricula",
            "marca",
            "modelo",
            "ano",
            "ativa",
            "criado_em",
            "atualizado_em",
        ]
        # Datas de auditoria são preenchidas automaticamente; nunca via API.
        read_only_fields = ["criado_em", "atualizado_em"]


class SeguroViaturaSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Calculado pela base RegistoComValidade; aparece no JSON mas não é editável.
    dias_para_expirar = serializers.IntegerField(read_only=True)

    class Meta:
        model = SeguroViatura
        fields = [
            "id",
            "viatura",
            "seguradora",
            "apolice",
            "data_inicio",
            "data_validade",
            "dias_para_expirar",
        ]


class InspecaoSerializer(serializers.ModelSerializer):
    dias_para_expirar = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inspecao
        fields = [
            "id",
            "viatura",
            "data_inspecao",
            "data_validade",
            "resultado",
            "dias_para_expirar",
        ]


class DespesaViaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DespesaViatura
        fields = ["id", "viatura", "descricao", "valor", "data"]
