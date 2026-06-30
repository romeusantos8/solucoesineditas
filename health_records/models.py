"""
Models da app de Fichas Médicas.

⚠️ DADOS DE SAÚDE — categoria especial ao abrigo do RGPD (art. 9.º). Esta app
trata aptidão médica dos funcionários. Medidas já aplicadas:
- acesso restrito (ver views: só staff/admin);
- separada das outras apps, para facilitar controlo de acesso e auditoria.

# TODO RGPD (fase seguinte, antes de produção real com dados verdadeiros):
#   - cifrar os campos sensíveis na base de dados (ex.: django-cryptography ou
#     pgcrypto), não os guardar em claro;
#   - registo de acessos (quem consultou que ficha e quando);
#   - política de retenção / minimização.
"""

from django.core.exceptions import ValidationError
from django.db import models

from config.common import RegistoComAuditoria, RegistoComValidade
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
    medico = models.CharField("Médico / entidade", max_length=160, blank=True)
    observacoes = models.TextField("Observações", blank=True)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

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
