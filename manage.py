#!/usr/bin/env python
"""Utilitário de linha de comandos do Django (corre tarefas administrativas)."""

import os
import sys


def main():
    """Executa tarefas administrativas (runserver, migrate, createsuperuser, ...)."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Tens a certeza de que está "
            "instalado e disponível na variável de ambiente PYTHONPATH? Esqueceste-te "
            "de ativar o ambiente virtual (venv)?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
