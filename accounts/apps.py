from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    App de autenticação / utilizadores.

    Mantém o LOGIN separado da lógica de negócio (viaturas, equipamentos).
    Por agora apoia-se inteiramente no User e nos Groups que já vêm com o Django.
    No futuro, é aqui que viverá, por exemplo, um modelo de Perfil ou a ligação
    a papéis/roles — sem misturar nada disso com o domínio de frota/equipamentos.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
