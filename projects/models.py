"""
Models da app de Clientes e Obras.

Estrutura: Cliente tem várias Obras; uma Obra aloca vários Funcionários (tabela
intermédia `AlocacaoFuncionario` com o seu período). Os equipamentos de uma obra
são DERIVADOS dos funcionários alocados — cada Equipamento tem um `responsavel`
(ver equipment/models.py), não há alocação direta de equipamento à obra.
"""

from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from config.common import RegistoComAuditoria, validar_nif
from employees.models import Funcionario


class Cliente(RegistoComAuditoria):
    """Cliente da empresa, dono de uma ou mais obras."""

    nome = models.CharField("Nome", max_length=160)
    nif = models.CharField("NIF", max_length=9, unique=True, null=True, blank=True)
    email = models.EmailField("Email", blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    # Timestamps e auditoria de utilizador vêm de RegistoComAuditoria.

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def clean(self):
        if self.nif:
            try:
                validar_nif(self.nif)
            except ValidationError as exc:
                raise ValidationError({"nif": exc.messages})


class Obra(RegistoComAuditoria):
    """Obra de um cliente. Aloca funcionários e equipamentos (via `through`)."""

    class Estado(models.TextChoices):
        PLANEADA = "planeada", "Planeada"
        EM_CURSO = "em_curso", "Em curso"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="obras",
        verbose_name="Cliente",
    )
    nome = models.CharField("Nome", max_length=160)
    descricao = models.TextField("Descrição", blank=True)
    data_inicio = models.DateField("Data de início")
    data_fim_prevista = models.DateField("Data de fim prevista", null=True, blank=True)
    estado = models.CharField(
        "Estado",
        max_length=12,
        choices=Estado.choices,
        default=Estado.PLANEADA,
    )

    # Funcionários alocados à obra (escrita via endpoint AlocacaoFuncionario).
    # Os equipamentos numa obra são DERIVADOS: são os equipamentos dos
    # funcionários alocados (cada equipamento tem um `responsavel`). Não há
    # alocação direta de equipamento à obra.
    funcionarios = models.ManyToManyField(
        Funcionario,
        through="AlocacaoFuncionario",
        related_name="obras",
        verbose_name="Funcionários alocados",
    )
    # Timestamps e auditoria de utilizador vêm de RegistoComAuditoria.

    class Meta:
        verbose_name = "Obra"
        verbose_name_plural = "Obras"
        ordering = ["-data_inicio"]

    def __str__(self):
        return f"{self.nome} ({self.cliente.nome})"

    def clean(self):
        # Fim previsto não pode ser antes do início.
        if (
            self.data_fim_prevista
            and self.data_inicio
            and self.data_fim_prevista < self.data_inicio
        ):
            raise ValidationError(
                {"data_fim_prevista": "Não pode ser anterior à data de início."}
            )


class AlocacaoBase(RegistoComAuditoria):
    """
    Base abstrata das alocações a uma obra. Cada alocação tem o seu período;
    data_fim nula = ainda alocado. A regra "só ativos" e a coerência das datas
    ficam no clean() das subclasses (que conhecem o recurso concreto).
    """

    obra = models.ForeignKey("Obra", on_delete=models.CASCADE, verbose_name="Obra")
    data_inicio = models.DateField("Data de início")
    data_fim = models.DateField("Data de fim", null=True, blank=True)

    class Meta:
        abstract = True

    def _validar_datas(self):
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError(
                {"data_fim": "Não pode ser anterior à data de início."}
            )
        # O fim da alocação não pode ultrapassar o fim previsto da obra (quando a
        # obra tem um fim previsto; se não tiver, não há limite superior).
        if self.data_fim and self.obra_id:
            fim_obra = self.obra.data_fim_prevista
            if fim_obra and self.data_fim > fim_obra:
                raise ValidationError(
                    {
                        "data_fim": (
                            "Não pode ser depois do fim previsto da obra "
                            f"({fim_obra})."
                        )
                    }
                )


class AlocacaoFuncionario(AlocacaoBase):
    """Alocação de um funcionário a uma obra, com período próprio."""

    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.PROTECT, verbose_name="Funcionário"
    )

    class Meta:
        verbose_name = "Alocação de funcionário"
        verbose_name_plural = "Alocações de funcionários"
        # Ordenação explícita: sem ela, a paginação pode devolver linhas em ordem
        # inconsistente entre pedidos (mesma alocação em duas páginas ou nenhuma).
        ordering = ["-data_inicio"]
        # O mesmo funcionário não pode estar duas vezes na mesma obra.
        unique_together = ("obra", "funcionario")

    def __str__(self):
        return f"{self.funcionario.nome} @ {self.obra.nome}"

    def clean(self):
        self._validar_datas()
        # Não se aloca um funcionário inativo (ex.: já saiu da empresa).
        if self.funcionario_id and not self.funcionario.ativo:
            raise ValidationError(
                {"funcionario": "Não é possível alocar um funcionário inativo."}
            )


class AutoObra(RegistoComAuditoria):
    """
    Auto mensal de uma obra: o que se faturou (ou vai faturar) num dado mês. É a
    base do relatório de faturação por obra. Cada auto pertence a um mês/ano e
    tem um valor; o `estado` distingue o que já foi faturado do que falta.
    """

    class Estado(models.TextChoices):
        POR_FATURAR = "por_faturar", "Por faturar"
        FATURADO = "faturado", "Faturado"

    obra = models.ForeignKey(
        Obra,
        on_delete=models.PROTECT,  # não se apaga uma obra com autos (histórico)
        related_name="autos",
        verbose_name="Obra",
    )
    ano = models.PositiveIntegerField(
        "Ano",
        # Limite inferior defensivo; o superior fica no clean() (ano-atual+1).
        validators=[MinValueValidator(2000)],
    )
    mes = models.PositiveSmallIntegerField(
        "Mês",
        validators=[MinValueValidator(1)],  # o máximo (12) é validado no clean()
    )
    valor = models.DecimalField(
        "Valor (€)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    descricao = models.CharField("Descrição", max_length=200, blank=True)
    estado = models.CharField(
        "Estado",
        max_length=12,
        choices=Estado.choices,
        default=Estado.POR_FATURAR,
    )
    # Timestamps e auditoria de utilizador vêm de RegistoComAuditoria.

    class Meta:
        verbose_name = "Auto de obra"
        verbose_name_plural = "Autos de obras"
        # Mais recentes primeiro (ano, depois mês). Ordenação explícita: sem ela
        # a paginação pode devolver linhas em ordem inconsistente entre pedidos.
        ordering = ["-ano", "-mes"]
        # Um auto por mês/ano por obra (evita duplicados do mesmo período).
        unique_together = ("obra", "ano", "mes")

    def __str__(self):
        return f"Auto {self.mes:02d}/{self.ano} — {self.obra.nome} ({self.valor}€)"

    def clean(self):
        # O mês tem de estar entre 1 e 12 (o validator só cobre o mínimo).
        if self.mes is not None and self.mes > 12:
            raise ValidationError({"mes": "O mês tem de estar entre 1 e 12."})
        # O ano não pode ser no futuro (além do próximo, para autos já previstos).
        if self.ano is not None and self.ano > date.today().year + 1:
            raise ValidationError(
                {"ano": f"O ano não pode ser superior a {date.today().year + 1}."}
            )
