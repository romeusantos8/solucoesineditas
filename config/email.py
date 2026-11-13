"""
Backend de email do Django que envia pela API HTTP do Resend. O plano Hobby do
Railway bloqueia as portas SMTP, por isso o backend SMTP do Django não serve lá.
"""

import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

URL_RESEND = "https://api.resend.com/emails"


class ResendBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        enviados = 0
        for mensagem in email_messages:
            try:
                self._enviar(mensagem)
                enviados += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return enviados

    def _enviar(self, mensagem):
        dados = {
            "from": mensagem.from_email,
            "to": mensagem.to,
            "subject": mensagem.subject,
            "text": mensagem.body,
        }
        for conteudo, tipo in getattr(mensagem, "alternatives", []):
            if tipo == "text/html":
                dados["html"] = conteudo
        pedido = urllib.request.Request(
            URL_RESEND,
            data=json.dumps(dados).encode(),
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
                # A API recusa pedidos sem User-Agent próprio (erro 1010).
                "User-Agent": "solucoes-ineditas-gestao/1.0",
            },
        )
        try:
            with urllib.request.urlopen(pedido, timeout=10):
                pass
        except urllib.error.HTTPError as exc:
            # O corpo da resposta explica o erro (ex.: domínio por verificar).
            detalhe = exc.read().decode(errors="replace")[:300]
            raise RuntimeError(f"Resend respondeu {exc.code}: {detalhe}") from exc
