"""
Serializers de Funcionários: validam a entrada e produzem o JSON de saída.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from config.common import AUDITORIA_FIELDS, ModelCleanSerializerMixin

from .models import DespesaFuncionario, Funcionario

User = get_user_model()


class FuncionarioSerializer(ModelCleanSerializerMixin, serializers.ModelSerializer):
    # Conta do portal de despesas (só leitura; gere-se em /acesso/).
    acesso = serializers.SerializerMethodField()

    class Meta:
        model = Funcionario
        fields = [
            "id",
            "nome",
            "nif",
            "funcao",
            "data_admissao",
            "ativo",
            "email",
            "telefone",
            "acesso",
            "criado_em",
            "atualizado_em",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = ["criado_em", "atualizado_em", *AUDITORIA_FIELDS]

    def get_acesso(self, obj) -> dict | None:
        if obj.utilizador is None:
            return None
        return {"username": obj.utilizador.username, "ativo": obj.utilizador.is_active}


class AcessoFuncionarioSerializer(serializers.Serializer):
    """
    Credenciais do portal (POST /api/funcionarios/{id}/acesso/). Serve para
    criar a conta e para a voltar a ativar/trocar a palavra-passe.
    """

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, valor):
        valor = valor.strip()
        # O username é do funcionário em causa (instance = Funcionario); só é
        # duplicado se pertencer a OUTRO User.
        existente = User.objects.filter(username__iexact=valor)
        if self.instance is not None and self.instance.utilizador_id:
            existente = existente.exclude(pk=self.instance.utilizador_id)
        if existente.exists():
            raise serializers.ValidationError("Já existe um utilizador com este nome.")
        return valor

    def validate(self, attrs):
        # Regras de palavra-passe do Django (AUTH_PASSWORD_VALIDATORS).
        utilizador = self.instance.utilizador if self.instance else None
        try:
            validate_password(attrs["password"], user=utilizador)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages})
        return attrs


class DespesaFuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DespesaFuncionario
        fields = [
            "id",
            "funcionario",
            "descricao",
            "valor",
            "data",
            *AUDITORIA_FIELDS,
        ]
        read_only_fields = [*AUDITORIA_FIELDS]


class MinhaDespesaSerializer(serializers.ModelSerializer):
    """
    Despesa vista pelo próprio funcionário no portal. Sem campo `funcionario`:
    é sempre o do utilizador autenticado (atribuído na view), para ninguém
    registar despesas em nome de outro.
    """

    class Meta:
        model = DespesaFuncionario
        fields = ["id", "descricao", "valor", "data", "criado_em"]
        read_only_fields = ["criado_em"]
