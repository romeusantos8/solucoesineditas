"""
Peças partilhadas entre várias apps de domínio (fleet, equipment, ...).

Aqui vive a base abstrata dos registos com prazo de validade. Um model
*abstrato* não cria tabela própria nem precisa de migração — serve apenas para
as subclasses herdarem campos e comportamento, evitando repetir código.
"""

from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError


def validar_nif(nif: str) -> None:
    """
    Valida um NIF português: 9 dígitos e dígito de controlo (checksum) correto.
    Levanta ValidationError se for inválido. O algoritmo é o oficial: soma
    ponderada dos 8 primeiros dígitos, e o 9º confirma o resultado.

    Partilhado por Funcionario e Cliente (ambos têm NIF).
    """
    if not nif.isdigit() or len(nif) != 9:
        raise DjangoValidationError("O NIF tem de ter exatamente 9 dígitos.")

    total = sum(int(nif[i]) * (9 - i) for i in range(8))
    resto = total % 11
    controlo = 0 if resto < 2 else 11 - resto
    if controlo != int(nif[8]):
        raise DjangoValidationError("NIF inválido (dígito de controlo não confere).")


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


# Nomes dos campos de auditoria, para os serializers os incluírem em fields /
# read_only_fields sem os repetirem à mão (e sem risco de divergirem do model).
AUDITORIA_FIELDS = ("criado_por", "atualizado_por")


class RegistoComAuditoria(models.Model):
    """
    Base que regista QUEM e QUANDO criou/alterou um registo. Para uma ferramenta
    de gestão empresarial (e RGPD), saber quem mexeu em quê (e quando) é requisito
    comum — e é barato agora, caro de acrescentar retroativamente. Centralizar
    aqui os timestamps evita repeti-los em cada model e cobre tudo de forma
    uniforme (incluindo os filhos: seguros, certificados, alocações, etc.).

    Os campos de utilizador são opcionais (null) porque registos criados fora de
    um pedido autenticado (ex.: shell, migração) não têm utilizador associado.
    on_delete=SET_NULL: apagar um utilizador não apaga o histórico que ele criou.
    """

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # não precisamos da relação inversa no User
        verbose_name="Criado por",
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Atualizado por",
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True


class AuditoriaAdminMixin:
    """
    Para ModelAdmins de models com RegistoComAuditoria: preenche
    criado_por/atualizado_por com o utilizador logado ao gravar pelo Admin, e
    mostra-os só de leitura. Sem isto, a auditoria só seria preenchida pela API.
    """

    readonly_fields = ("criado_por", "atualizado_por")

    def save_model(self, request, obj, form, change):
        if not change:  # criação
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)


class AuditoriaViewSetMixin:
    """
    Para ViewSets cujos models herdam de RegistoComAuditoria: preenche
    automaticamente criado_por (na criação) e atualizado_por (em cada gravação)
    com o utilizador autenticado do pedido. A view é o único sítio que conhece
    o request, por isso a atribuição vive aqui, não no serializer.
    """

    def perform_create(self, serializer):
        serializer.save(
            criado_por=self.request.user,
            atualizado_por=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(atualizado_por=self.request.user)


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
