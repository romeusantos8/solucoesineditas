"""
Models da app de Clientes e Obras.

Estrutura (README): Cliente tem várias Obras; uma Obra aloca vários Funcionários
e Equipamentos. As alocações são modeladas com tabelas intermédias explícitas
(`through`), para cada alocação guardar as suas próprias datas — assim fica
registado quem/o quê esteve numa obra e durante que período.
"""

from django.core.exceptions import ValidationError
from django.db import models

from config.common import RegistoComAuditoria, validar_nif
from employees.models import Funcionario
from equipment.models import Equipamento


class Cliente(RegistoComAuditoria):
    """Cliente da empresa, dono de uma ou mais obras."""

    nome = models.CharField("Nome", max_length=160)
    nif = models.CharField("NIF", max_length=9, unique=True, null=True, blank=True)
    email = models.EmailField("Email", blank=True)
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

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

    # Acesso de conveniência às entidades alocadas. A escrita faz-se pelos
    # endpoints das alocações (ver AlocacaoFuncionario/AlocacaoEquipamento).
    funcionarios = models.ManyToManyField(
        Funcionario,
        through="AlocacaoFuncionario",
        related_name="obras",
        verbose_name="Funcionários alocados",
    )
    equipamentos = models.ManyToManyField(
        Equipamento,
        through="AlocacaoEquipamento",
        related_name="obras",
        verbose_name="Equipamentos alocados",
    )

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

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


class AlocacaoEquipamento(AlocacaoBase):
    """Alocação de um equipamento a uma obra, com período próprio."""

    equipamento = models.ForeignKey(
        Equipamento, on_delete=models.PROTECT, verbose_name="Equipamento"
    )

    class Meta:
        verbose_name = "Alocação de equipamento"
        verbose_name_plural = "Alocações de equipamentos"
        unique_together = ("obra", "equipamento")

    def __str__(self):
        return f"{self.equipamento.nome} @ {self.obra.nome}"

    def clean(self):
        self._validar_datas()
        if self.equipamento_id and not self.equipamento.ativo:
            raise ValidationError(
                {"equipamento": "Não é possível alocar um equipamento inativo."}
            )
