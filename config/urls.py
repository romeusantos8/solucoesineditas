"""
Mapa de URLs principal do projeto (o "porteiro" que decide que código corre
para cada endereço).

A API vive toda sob /api/. A autenticação é por Token: o cliente faz POST a
/api/auth/token/ com username+password e recebe um token, que depois envia no
cabeçalho `Authorization: Token <token>` em cada pedido.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Painel de administração do Django, onde vais inserir e ver dados reais.
    path("admin/", admin.site.urls),

    # API REST (CRUD de viaturas, equipamentos e tudo o que lhes pertence).
    path("api/", include("fleet.urls")),
    path("api/", include("equipment.urls")),

    # Dashboard de alertas: prazos a expirar (GET /api/alerts/?dias=N).
    path("api/", include("alerts.urls")),

    # Login da API: devolve o token a usar nos restantes pedidos.
    path("api/auth/token/", obtain_auth_token, name="api-token"),

    # Login/logout da Browsable API (para testar autenticado no browser).
    path("api-auth/", include("rest_framework.urls")),
]
