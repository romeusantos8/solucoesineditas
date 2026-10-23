"""
Views da app de utilizadores.

GET /api/eu/ → quem está autenticado e que ecrã o frontend lhe deve mostrar:
- "gestao": app principal;
- "funcionario": portal de despesas;
- "sem_acesso": conta de funcionário cujo funcionário foi desativado.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import funcionario_do_utilizador, tem_acesso_gestao


@extend_schema(
    tags=["Autenticação"],
    responses=inline_serializer(
        "Eu",
        {
            "username": serializers.CharField(),
            "perfil": serializers.ChoiceField(["gestao", "funcionario", "sem_acesso"]),
            "funcionario": serializers.DictField(allow_null=True),
        },
    ),
)
class EuView(APIView):
    # Qualquer autenticado: é precisamente o que diz a cada um o que pode ver.
    permission_classes = [IsAuthenticated]

    def get(self, request):
        funcionario = funcionario_do_utilizador(request.user)
        if tem_acesso_gestao(request.user):
            perfil = "gestao"
        elif funcionario.ativo:
            perfil = "funcionario"
        else:
            perfil = "sem_acesso"
        return Response({
            "username": request.user.get_username(),
            "perfil": perfil,
            "funcionario": (
                {"id": funcionario.id, "nome": funcionario.nome} if funcionario else None
            ),
        })
