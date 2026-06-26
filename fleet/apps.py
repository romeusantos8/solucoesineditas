from django.apps import AppConfig


class FleetConfig(AppConfig):
    """
    App de Frota: Viaturas e tudo o que lhes está associado
    (seguros, inspeções e despesas).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "fleet"
