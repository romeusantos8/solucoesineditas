from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    name = 'employees'

    def ready(self):
        from . import signals  # noqa: F401  (regista os sinais)
