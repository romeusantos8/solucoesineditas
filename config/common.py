"""
Peças partilhadas entre várias apps de domínio (fleet, equipment, ...).

Aqui vive a base abstrata dos registos com prazo de validade. Um model
*abstrato* não cria tabela própria nem precisa de migração — serve apenas para
as subclasses herdarem campos e comportamento, evitando repetir código.
"""

from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError


class RegistoComValidade(models.Model):
    """
    Base para qualquer registo que expira numa data (seguros, inspeções,
    certificados). Centraliza o campo `data_validade` e o cálculo de quantos
    dias faltam, para o dashboard de alertas (Passo 4) tratar todos por igual.
    """

    # A data que alimenta os alertas. db_index porque o endpoint de alertas vai
    # filtrar/ordenar por este campo com frequência.
    data_validade = models.DateField("Data de validade", db_index=True)

    class Meta:
        abstract = True

    @property
    def dias_para_expirar(self):
        """
        Dias até expirar a contar de hoje. Negativo = já expirou; 0 = expira
        hoje. Calculado a partir da data atual, por isso está sempre correto
        sem precisar de ser atualizado na base de dados.
        """
        return (self.data_validade - date.today()).days

    @property
    def expirado(self):
        return self.dias_para_expirar < 0


class ModelCleanSerializerMixin:
    """
    Faz um ModelSerializer correr o `clean()`/`full_clean()` do model na
    validação, para que as regras de negócio definidas UMA vez no model
    (matrícula normalizada, datas coerentes, etc.) valham também na API — sem
    duplicar a lógica. As mensagens do Django são convertidas para o formato
    de erro do DRF (resposta 400 com os campos certos).
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Constrói uma instância (não gravada) com os dados já validados pelo
        # serializer. Em update, parte da instância existente para não perder
        # campos que não vêm no payload (PATCH parcial).
        instance = self.instance if self.instance is not None else self.Meta.model()
        for campo, valor in attrs.items():
            setattr(instance, campo, valor)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise DRFValidationError(serializers.as_serializer_error(exc))
        # O clean() pode normalizar campos (ex.: matrícula em maiúsculas). Relê
        # os valores da instância de volta para attrs, para que essas mudanças
        # cheguem à base de dados e à resposta.
        for campo in attrs:
            attrs[campo] = getattr(instance, campo)
        return attrs
