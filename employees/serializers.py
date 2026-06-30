"""
Serializers de Funcionários: validam a entrada e produzem o JSON de saída.
"""

from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import DespesaFuncionario, Funcionario


class FuncionarioSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = [
            "id",
            "nome",
            "nif",
            "funcao",
            "data_admissao",
            "ativo",
            "email",
            "telefone",
            "criado_em",
            "atualizado_em",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]


class DespesaFuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DespesaFuncionario
        fields = [
            "id",
            "funcionario",
            "descricao",
            "valor",
            "data",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]
