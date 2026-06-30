"""
Serializer da Ficha Médica. Dados sensíveis (RGPD) — ver views para o acesso.
"""

from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import FichaMedica


class FichaMedicaSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    dias_para_expirar = serializers.IntegerField(read_only=True)

    class Meta:
        model = FichaMedica
        fields = [
            "id",
            "funcionario",
            "aptidao",
            "data_exame",
            "data_validade",
            "dias_para_expirar",
            "medico",
            "observacoes",
            "criado_em",
            "atualizado_em",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]
