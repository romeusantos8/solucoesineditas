"""
Models da app de Funcionários.

Entidade central: Funcionario, com as suas despesas. Segue o mesmo padrão das
outras apps de domínio (auditoria via RegistoComAuditoria; validações no
clean()).

NOTA RGPD: a ficha médica do funcionário (dados de saúde, categoria especial)
NÃO vive aqui. Será uma entidade própria, numa fase posterior, com cifragem dos
campos e acesso restrito por perfil. Aqui ficam apenas dados administrativos.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from config.common import RegistoComAuditoria, validar_nif


class Funcionario(RegistoComAuditoria):
    """Um funcionário da empresa (dados administrativos)."""

    nome = models.CharField("Nome", max_length=160)
    # Único quando preenchido; null permite vários funcionários sem NIF sem
    # colidirem na constraint de unicidade.
    nif = models.CharField(
        "NIF", max_length=9, unique=True, null=True, blank=True
    )
    funcao = models.CharField("Função", max_length=80)
    data_admissao = models.DateField("Data de admissão")
    ativo = models.BooleanField("Ativo", default=True)
    email = models.EmailField("Email", blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        # NIF só é validado quando preenchido (é opcional). Associamos o erro ao
        # campo `nif` (e não geral) para a API/Admin o mostrarem no sítio certo.
        if self.nif:
            try:
                validar_nif(self.nif)
            except ValidationError as exc:
                raise ValidationError({"nif": exc.messages})


class DespesaFuncionario(RegistoComAuditoria):
    """Despesa associada a um funcionário (ex.: formação, deslocação)."""

    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,  # não deixa apagar funcionários com histórico
        related_name="despesas",
        verbose_name="Funcionário",
    )
    descricao = models.CharField("Descrição", max_length=200)
    valor = models.DecimalField(
        "Valor (€)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    data = models.DateField("Data")

    class Meta:
        verbose_name = "Despesa de funcionário"
        verbose_name_plural = "Despesas de funcionários"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.descricao} — {self.valor}€ ({self.funcionario.nome})"
