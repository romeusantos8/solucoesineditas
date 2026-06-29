"""
Models da app de Frota (MVC: estes são os "Model").

Entidade central: Viatura. À volta dela giram os seus seguros, inspeções e
despesas. Os registos com prazo (seguros, inspeções) herdam de
RegistoComValidade para alimentarem o dashboard de alertas de forma uniforme.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from config.common import RegistoComValidade

# A viatura mais antiga plausível e a margem para o futuro (modelos do ano
# seguinte já à venda). Usado para validar o campo `ano`.
ANO_MINIMO = 1950


def _ano_maximo():
    # Função (não constante) para acompanhar a passagem dos anos.
    return date.today().year + 1


class Viatura(models.Model):
    """Uma viatura da empresa, identificada pela matrícula."""

    matricula = models.CharField("Matrícula", max_length=20, unique=True)
    marca = models.CharField("Marca", max_length=60)
    modelo = models.CharField("Modelo", max_length=60)
    ano = models.PositiveIntegerField(
        "Ano",
        null=True,
        blank=True,
        validators=[MinValueValidator(ANO_MINIMO)],  # limite inferior fixo
    )
    # `ativa=False` = viatura abatida/vendida, mantida só para histórico.
    ativa = models.BooleanField("Ativa", default=True)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Viatura"
        verbose_name_plural = "Viaturas"
        ordering = ["matricula"]

    def __str__(self):
        return f"{self.matricula} ({self.marca} {self.modelo})"

    def clean(self):
        # Normaliza a matrícula: maiúsculas e sem espaços nas pontas, para não
        # haver duplicados disfarçados (' aa-00 ' vs 'AA-00').
        if self.matricula:
            self.matricula = self.matricula.strip().upper()
        # Limite superior do ano depende do ano atual, por isso fica aqui (o
        # MinValueValidator trata do limite inferior).
        if self.ano is not None and self.ano > _ano_maximo():
            raise ValidationError(
                {"ano": f"O ano não pode ser superior a {_ano_maximo()}."}
            )


class SeguroViatura(RegistoComValidade):
    """Apólice de seguro de uma viatura. `data_validade` herdada da base."""

    viatura = models.ForeignKey(
        Viatura,
        on_delete=models.PROTECT,  # não deixa apagar viaturas com histórico
        related_name="seguros",
        verbose_name="Viatura",
    )
    seguradora = models.CharField("Seguradora", max_length=80)
    apolice = models.CharField("Nº de apólice", max_length=60)
    data_inicio = models.DateField("Data de início")

    class Meta:
        verbose_name = "Seguro de viatura"
        verbose_name_plural = "Seguros de viaturas"
        ordering = ["data_validade"]

    def __str__(self):
        return f"Seguro {self.seguradora} — {self.viatura.matricula}"

    def clean(self):
        # A validade tem de ser posterior ao início da apólice.
        if (
            self.data_inicio
            and self.data_validade
            and self.data_validade <= self.data_inicio
        ):
            raise ValidationError(
                {"data_validade": "A validade tem de ser posterior à data de início."}
            )


class Inspecao(RegistoComValidade):
    """Inspeção periódica. `data_validade` = data da próxima inspeção."""

    class Resultado(models.TextChoices):
        APROVADO = "aprovado", "Aprovado"
        REPROVADO = "reprovado", "Reprovado"

    viatura = models.ForeignKey(
        Viatura,
        on_delete=models.PROTECT,
        related_name="inspecoes",
        verbose_name="Viatura",
    )
    data_inspecao = models.DateField("Data da inspeção")
    resultado = models.CharField(
        "Resultado",
        max_length=10,
        choices=Resultado.choices,
        default=Resultado.APROVADO,
    )

    class Meta:
        verbose_name = "Inspeção"
        verbose_name_plural = "Inspeções"
        ordering = ["data_validade"]

    def __str__(self):
        return f"Inspeção {self.viatura.matricula} — {self.data_inspecao}"


class DespesaViatura(models.Model):
    """Despesa pontual de uma viatura. Não tem prazo, não gera alertas."""

    viatura = models.ForeignKey(
        Viatura,
        on_delete=models.PROTECT,
        related_name="despesas",
        verbose_name="Viatura",
    )
    descricao = models.CharField("Descrição", max_length=200)
    valor = models.DecimalField(
        "Valor (€)",
        max_digits=10,
        decimal_places=2,
        # Valor mínimo de 1 cêntimo: rejeita 0 e negativos.
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    data = models.DateField("Data")

    class Meta:
        verbose_name = "Despesa de viatura"
        verbose_name_plural = "Despesas de viaturas"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.descricao} — {self.valor}€ ({self.viatura.matricula})"
