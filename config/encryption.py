"""
Cifragem de campos sensíveis ao nível da aplicação (RGPD).

`EncryptedTextField` cifra o valor antes de o gravar na base de dados e decifra-o
ao ler. Quem aceda diretamente à BD vê apenas texto cifrado — importante para
dados de categoria especial (saúde), como as fichas médicas.

Usa Fernet (AES-128 em modo CBC + HMAC) da biblioteca `cryptography`. A chave
vem do ambiente (FIELD_ENCRYPTION_KEY), NUNCA do código. Gerar uma chave:

    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

⚠️ A chave é o segredo que protege os dados. Se a perderes, os dados cifrados
ficam irrecuperáveis. Guarda-a no gestor de segredos do alojamento (Railway),
não no git.
"""

from cryptography.fernet import Fernet, InvalidToken
from decouple import config
from django.core.exceptions import ImproperlyConfigured
from django.db import models

# Prefixo que marca um valor já cifrado, para distinguir de dados antigos em
# claro (ex.: criados antes da cifragem) e evitar tentar decifrá-los.
_PREFIXO = "enc:"


def _fernet() -> Fernet:
    chave = config("FIELD_ENCRYPTION_KEY", default="")
    if not chave:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY em falta. Gera uma com:\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"'
        )
    try:
        return Fernet(chave.encode())
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY inválida (tem de ser uma chave Fernet base64)."
        ) from exc


class EncryptedTextField(models.TextField):
    """
    TextField cujo conteúdo é cifrado em repouso (na base de dados). A cifragem
    é transparente: no código Python trabalhas com o texto normal.
    """

    def get_prep_value(self, value):
        # Python -> BD: cifra antes de gravar.
        if value is None or value == "":
            return value
        token = _fernet().encrypt(str(value).encode()).decode()
        return f"{_PREFIXO}{token}"

    def from_db_value(self, value, expression, connection):
        # BD -> Python: decifra ao ler.
        if value is None or value == "":
            return value
        if not value.startswith(_PREFIXO):
            # Valor antigo em claro (não cifrado): devolve como está.
            return value
        token = value[len(_PREFIXO):]
        try:
            return _fernet().decrypt(token.encode()).decode()
        except InvalidToken:
            # Chave errada/dados corrompidos — não rebenta a app, mas sinaliza.
            return "[dados cifrados ilegíveis]"
