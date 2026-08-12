"""
Serializers da Frota (numa API, o "template"/View é o JSON que estes produzem).

Um serializer faz duas coisas: valida os dados que entram (POST/PUT) e converte
os objetos do model em JSON na saída. As validações de negócio que falaste
adicionar mais tarde vivem aqui (métodos validate_<campo> / validate).
"""

from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import DespesaViatura, Inspecao, SeguroViatura, Viatura


class ViaturaSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Nome do responsável, só de leitura, para as listas mostrarem o nome sem
    # um pedido extra. Mesmo padrão do EquipamentoSerializer.
    responsavel_nome = serializers.CharField(
        source="responsavel.nome", read_only=True, default=None
    )

    class Meta:
        model = Viatura
        fields = [
            "id",
            "matricula",
            "marca",
            "modelo",
            "ano",
            "ativa",
            "responsavel",
            "responsavel_nome",
            "criado_em",
            "atualizado_em",
            *AUDITORIA_FIELDS,
        ]
        # Datas de auditoria são preenchidas automaticamente; nunca via API.
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]


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
            "valor",
            "dias_para_expirar",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]


class InspecaoSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
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
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]


class DespesaViaturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DespesaViatura
        fields = ["id", "viatura", "descricao", "valor", "data", *AUDITORIA_FIELDS]
        read_only_fields = [*AUDITORIA_FIELDS]
