"""
Models da app de Fichas Médicas.

⚠️ DADOS DE SAÚDE — categoria especial ao abrigo do RGPD (art. 9.º). Esta app
trata aptidão médica dos funcionários. Medidas já aplicadas:
- acesso restrito (ver views: só staff/admin);
- separada das outras apps, para facilitar controlo de acesso e auditoria;
- campos de texto livre (médico, observações) CIFRADOS em repouso na BD, com
  chave fora do código (ver config/encryption.py e FIELD_ENCRYPTION_KEY).

# TODO RGPD (melhorias futuras, não bloqueantes):
#   - registo de acessos (quem consultou que ficha e quando);
#   - política de retenção / minimização.
"""

from django.core.exceptions import ValidationError
from django.db import models

from config.common import RegistoComAuditoria, RegistoComValidade
from config.encryption import EncryptedTextField
from employees.models import Funcionario


class FichaMedica(RegistoComValidade, RegistoComAuditoria):
    """
    Ficha de aptidão médica de um funcionário. Cada funcionário tem no máximo
    uma ficha corrente (OneToOne). `data_validade` (herdada) = validade do
    exame, e alimenta o dashboard de alertas.
    """

    class Aptidao(models.TextChoices):
        APTO = "apto", "Apto"
        APTO_COM_RESTRICOES = "apto_restricoes", "Apto com restrições"
        NAO_APTO = "nao_apto", "Não apto"

    funcionario = models.OneToOneField(
        Funcionario,
        on_delete=models.PROTECT,
        related_name="ficha_medica",
        verbose_name="Funcionário",
    )
    aptidao = models.CharField(
        "Aptidão", max_length=20, choices=Aptidao.choices
    )
    data_exame = models.DateField("Data do exame")
    # data_validade herdada de RegistoComValidade (validade do exame).
    # `medico` e `observacoes` são CIFRADOS na BD (texto livre, potencialmente
    # clínico — dados de saúde RGPD). Ver config/encryption.py.
    medico = EncryptedTextField("Médico / entidade", blank=True)
    observacoes = EncryptedTextField("Observações", blank=True)
    # Timestamps e auditoria de utilizador vêm de RegistoComAuditoria.

    class Meta:
        verbose_name = "Ficha médica"
        verbose_name_plural = "Fichas médicas"
        ordering = ["data_validade"]

    def __str__(self):
        # Não expõe dados clínicos no texto — só identifica a ficha.
        return f"Ficha médica de {self.funcionario.nome}"

    def clean(self):
        if (
            self.data_exame
            and self.data_validade
            and self.data_validade <= self.data_exame
        ):
            raise ValidationError(
                {"data_validade": "A validade tem de ser posterior à data do exame."}
            )
