"""
Models da app de Equipamentos (MVC: estes são os "Model").

Entidade central: Equipamento, com os seus Certificados. O certificado tem
prazo de validade, por isso herda de RegistoComValidade e entra nos alertas.
"""

from django.core.exceptions import ValidationError
from django.db import models

from config.common import RegistoComAuditoria, RegistoComValidade


class Equipamento(RegistoComAuditoria):
    """Um equipamento da empresa."""

    nome = models.CharField("Nome", max_length=120)
    # Único quando preenchido; null=True permite vários equipamentos sem nº de
    # série sem colidirem na constraint de unicidade.
    numero_serie = models.CharField(
        "Nº de série", max_length=80, unique=True, null=True, blank=True
    )
    ativo = models.BooleanField("Ativo", default=True)
    # Funcionário responsável pelo equipamento (1 equipamento → no máx. 1
    # funcionário; um funcionário pode ter vários). String p/ evitar import
    # circular. SET_NULL: desatribuir o funcionário deixa o equipamento sem dono,
    # não o apaga.
    responsavel = models.ForeignKey(
        "employees.Funcionario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipamentos",
        verbose_name="Responsável",
    )
    # Timestamps e auditoria de utilizador vêm de RegistoComAuditoria.

    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"
        ordering = ["nome"]

    def __str__(self):
        if self.numero_serie:
            return f"{self.nome} ({self.numero_serie})"
        return self.nome


class Certificado(RegistoComValidade, RegistoComAuditoria):
    """Certificação de um equipamento. `data_validade` herdada da base."""

    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.PROTECT,  # não deixa apagar equipamentos com histórico
        related_name="certificados",
        verbose_name="Equipamento",
    )
    tipo = models.CharField("Tipo de certificação", max_length=120)
    data_emissao = models.DateField("Data de emissão")

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        ordering = ["data_validade"]

    def __str__(self):
        return f"{self.tipo} — {self.equipamento.nome}"

    def clean(self):
        # A validade tem de ser posterior à emissão.
        if (
            self.data_emissao
            and self.data_validade
            and self.data_validade <= self.data_emissao
        ):
            raise ValidationError(
                {"data_validade": "A validade tem de ser posterior à data de emissão."}
            )
