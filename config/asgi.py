"""
Ponto de entrada ASGI — alternativa ao WSGI para servidores assíncronos.
Não o usamos diretamente neste MVP, mas o Django cria-o por convenção.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
