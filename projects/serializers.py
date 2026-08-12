"""
Serializers de Clientes e Obras.

A alocação de funcionários tem endpoint próprio para escrita; na leitura de uma
Obra mostramos as alocações aninhadas (read-only). Os equipamentos de uma obra
são DERIVADOS: são os equipamentos dos funcionários alocados (cada equipamento
tem um `responsavel`), apresentados como lista só-de-leitura.
"""

from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import AlocacaoFuncionario, AutoObra, Cliente, Obra


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


class AutoObraSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Rótulo legível do estado (ex.: "Por faturar"), para a UI o mostrar direto.
    estado_display = serializers.CharField(
        source="get_estado_display", read_only=True
    )

    class Meta:
        model = AutoObra
        fields = [
            "id", "obra", "ano", "mes", "valor", "descricao",
            "estado", "estado_display", *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]


class ObraSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Alocações de funcionários aninhadas só na LEITURA (escrita via /api/alocacoes-funcionarios/).
    alocacoes_funcionarios = AlocacaoFuncionarioSerializer(
        source="alocacaofuncionario_set", many=True, read_only=True
    )
    # Equipamentos derivados: os dos funcionários alocados à obra. Só leitura.
    equipamentos_derivados = serializers.SerializerMethodField()

    class Meta:
        model = Obra
        fields = [
            "id", "cliente", "nome", "descricao",
            "data_inicio", "data_fim_prevista", "estado",
            "alocacoes_funcionarios", "equipamentos_derivados",
            "criado_em", "atualizado_em", *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]

    def get_equipamentos_derivados(self, obra):
        """
        Junta os equipamentos de todos os funcionários alocados à obra. Cada item
        indica o equipamento e de que funcionário vem.
        """
        itens = []
        vistos = set()
        for alocacao in obra.alocacaofuncionario_set.all():
            funcionario = alocacao.funcionario
            for equip in funcionario.equipamentos.all():
                if equip.id in vistos:
                    continue
                vistos.add(equip.id)
                itens.append({
                    "id": equip.id,
                    "nome": equip.nome,
                    "numero_serie": equip.numero_serie,
                    "funcionario_id": funcionario.id,
                    "funcionario_nome": funcionario.nome,
                })
        return itens
