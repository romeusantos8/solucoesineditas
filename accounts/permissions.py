"""
Permissões da API: separam a app de gestão do portal do funcionário.

Há dois tipos de utilizador:
- gestão: os utilizadores de sempre (admin/staff e outros sem funcionário
  associado) — usam a app principal inteira;
- funcionário: um User ligado a um Funcionario (`Funcionario.utilizador`) —
  só pode usar o portal (registar e ver as SUAS despesas).

`AcessoGestao` é a permissão por defeito de toda a API (DEFAULT_PERMISSION_CLASSES),
por isso um funcionário que tente chamar /api/viaturas/ ou /api/funcionarios/
leva 403. Staff tem sempre acesso à gestão, mesmo que esteja ligado a um
funcionário (ex.: o dono da empresa também regista as suas despesas).
"""

from rest_framework.permissions import BasePermission


def funcionario_do_utilizador(user):
    """Funcionario associado ao utilizador, ou None (gestão/anónimo)."""
    if not user or not user.is_authenticated:
        return None
    # A relação inversa do OneToOne levanta RelatedObjectDoesNotExist (que é
    # um AttributeError) quando não há funcionário: o getattr devolve None.
    return getattr(user, "funcionario", None)


def tem_acesso_gestao(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_staff or funcionario_do_utilizador(user) is None


class AcessoGestao(BasePermission):
    """App principal: autenticado e não é (só) uma conta de funcionário."""

    message = "Esta conta só tem acesso ao registo de despesas."

    def has_permission(self, request, view):
        return tem_acesso_gestao(request.user)


class AcessoFuncionario(BasePermission):
    """Portal do funcionário: conta ligada a um funcionário ativo."""

    message = "Esta conta não está associada a um funcionário ativo."

    def has_permission(self, request, view):
        funcionario = funcionario_do_utilizador(request.user)
        return funcionario is not None and funcionario.ativo
