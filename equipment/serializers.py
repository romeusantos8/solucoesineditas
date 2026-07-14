"""
Serializers de Equipamentos: validam a entrada e produzem o JSON de saída.
"""

from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import Certificado, Equipamento


class EquipamentoSerializer(serializers.ModelSerializer):
    # Nome do responsável (read-only) para a UI não ter de o ir buscar à parte.
    responsavel_nome = serializers.CharField(
        source="responsavel.nome", read_only=True, default=None
    )

    class Meta:
        model = Equipamento
        fields = [
            "id",
            "nome",
            "numero_serie",
            "ativo",
            "responsavel",
            "responsavel_nome",
            "criado_em",
            "atualizado_em",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]


class CertificadoSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Calculado pela base RegistoComValidade; só de leitura.
    dias_para_expirar = serializers.IntegerField(read_only=True)

    class Meta:
        model = Certificado
        fields = [
            "id",
            "equipamento",
            "tipo",
            "data_emissao",
            "data_validade",
            "dias_para_expirar",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]
