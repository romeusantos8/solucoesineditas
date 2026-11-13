"""
Email enviado à empresa quando um funcionário regista uma despesa no portal, com
o link assinado que permite marcá-la como paga sem iniciar sessão.
"""

import logging
import threading
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)

# O salt impede que uma assinatura de outra parte do Django sirva neste link.
SALT_PAGAMENTO = "employees.pagamento-despesa"
# O link dispensa login: quem o tiver vê a despesa e pode marcá-la como paga.
# Com prazo, um email antigo reencaminhado ou esquecido deixa de servir.
VALIDADE_LINK_PAGAMENTO = timedelta(days=30)


def token_pagamento(despesa):
    return signing.dumps(despesa.pk, salt=SALT_PAGAMENTO)


def despesa_do_token(token):
    """
    Devolve o id da despesa, ou levanta signing.BadSignature se o token for
    inválido ou tiver expirado (SignatureExpired é subclasse de BadSignature).
    """
    return signing.loads(token, salt=SALT_PAGAMENTO, max_age=VALIDADE_LINK_PAGAMENTO)


def _enviar(mensagem):
    # Corre fora do pedido: uma falha fica nos logs e a despesa já está gravada.
    try:
        mensagem.send()
    except Exception:
        logger.exception("Falha ao enviar o email de nova despesa")


def notificar_nova_despesa(despesa, request):
    """Envia o email numa thread, para o funcionário não ficar à espera."""
    try:
        if not settings.NOTIFICACAO_DESPESAS_EMAILS:
            return
        link = request.build_absolute_uri(
            reverse("confirmar-pagamento", args=[token_pagamento(despesa)])
        )
        contexto = {"despesa": despesa, "link": link}
        # A descrição não entra no assunto: é texto livre, e uma quebra de linha
        # num cabeçalho de email faz o Django recusar o envio.
        mensagem = EmailMultiAlternatives(
            subject=f"Nova despesa: {despesa.funcionario.nome} ({despesa.valor} €)",
            body=(
                f"{despesa.funcionario.nome} registou uma despesa.\n\n"
                f"Descrição: {despesa.descricao}\n"
                f"Valor: {despesa.valor} €\n"
                f"Data: {despesa.data:%d/%m/%Y}\n\n"
                f"Para a marcar como paga: {link}\n"
            ),
            to=settings.NOTIFICACAO_DESPESAS_EMAILS,
        )
        mensagem.attach_alternative(
            render_to_string("employees/email_nova_despesa.html", contexto), "text/html"
        )
        threading.Thread(target=_enviar, args=(mensagem,), daemon=True).start()
    except Exception:
        logger.exception("Falha ao preparar o email de nova despesa")
