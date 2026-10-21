"""
Sinais da app de Funcionários.

Apagar um funcionário com conta no portal deixaria o User solto — e um User sem
funcionário associado é tratado como utilizador de GESTÃO (ver
accounts/permissions.py). Por isso a conta é desativada no mesmo momento. Um
sinal (e não um delete() no model) apanha também os apagamentos em massa do
Admin, que não chamam o delete() de cada objeto.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Funcionario


@receiver(post_delete, sender=Funcionario)
def desativar_conta_do_funcionario(sender, instance, **kwargs):
    if instance.utilizador_id:
        get_user_model().objects.filter(pk=instance.utilizador_id).update(
            is_active=False
        )
