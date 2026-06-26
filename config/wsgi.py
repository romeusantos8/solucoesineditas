"""
Ponto de entrada WSGI — é por aqui que um servidor de produção (ex.: gunicorn,
no Railway/Render) liga à tua aplicação Django.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
