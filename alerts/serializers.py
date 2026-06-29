"""
Serializer da resposta de alertas.

Não está ligado a um model: descreve a *forma comum* de um alerta, para onde
convertemos seguros, inspeções e certificados (que são models diferentes). Só
serve para saída (read-only), por isso usa Serializer simples, não ModelSerializer.
"""

from rest_framework import serializers


class AlertaSerializer(serializers.Serializer):
    tipo = serializers.CharField()              # "seguro" | "inspecao" | "certificado"
    descricao = serializers.CharField()         # texto legível (o __str__ do registo)
    data_validade = serializers.DateField()
    dias_para_expirar = serializers.IntegerField()
    expirado = serializers.BooleanField()
    recurso = serializers.CharField()           # "viatura" | "equipamento"
    recurso_id = serializers.IntegerField()     # id da viatura/equipamento associado
    registo_id = serializers.IntegerField()     # id do próprio seguro/inspeção/certificado
