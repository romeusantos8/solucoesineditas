from django.apps import AppConfig


class AlertsConfig(AppConfig):
    """
    App do dashboard de Alertas.

    Não tem models próprios: a sua função é apenas LER as outras apps
    (seguros, inspeções, certificados) e agregar os prazos a expirar.
    Por isso também não tem pasta de migrações.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "alerts"
