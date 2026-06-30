"""
Serializers de Clientes e Obras.

As alocações (funcionários/equipamentos numa obra) têm endpoints próprios para
escrita. Na leitura de uma Obra, mostramos as alocações aninhadas (read-only)
para o cliente ver de uma vez quem/o quê está alocado.
"""

from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import (
    AlocacaoEquipamento,
    AlocacaoFuncionario,
    Cliente,
    Obra,
)


class ClienteSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id", "nome", "nif", "email", "telefone", "ativo",
            "criado_em", "atualizado_em", *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]


class AlocacaoFuncionarioSerializer(
    ModelCleanSerializerMixin, serializers.ModelSerializer
):
    # Nome legível do funcionário, para a UI não ter de ir buscá-lo à parte.
    funcionario_nome = serializers.CharField(
        source="funcionario.nome", read_only=True
    )

    class Meta:
        model = AlocacaoFuncionario
        fields = [
            "id", "obra", "funcionario", "funcionario_nome",
            "data_inicio", "data_fim", *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]


class AlocacaoEquipamentoSerializer(
    ModelCleanSerializerMixin, serializers.ModelSerializer
):
    equipamento_nome = serializers.CharField(
        source="equipamento.nome", read_only=True
    )

    class Meta:
        model = AlocacaoEquipamento
        fields = [
            "id", "obra", "equipamento", "equipamento_nome",
            "data_inicio", "data_fim", *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]


class ObraSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Alocações aninhadas só na LEITURA (escrita via /api/alocacoes-*/).
    alocacoes_funcionarios = AlocacaoFuncionarioSerializer(
        source="alocacaofuncionario_set", many=True, read_only=True
    )
    alocacoes_equipamentos = AlocacaoEquipamentoSerializer(
        source="alocacaoequipamento_set", many=True, read_only=True
    )

    class Meta:
        model = Obra
        fields = [
            "id", "cliente", "nome", "descricao",
            "data_inicio", "data_fim_prevista", "estado",
            "alocacoes_funcionarios", "alocacoes_equipamentos",
            "criado_em", "atualizado_em", *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]
