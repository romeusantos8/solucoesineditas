"""
Mapa de URLs principal do projeto (o "porteiro" que decide que código corre
para cada endereço).

Por agora só temos o Admin. No Passo 3 vamos incluir aqui as URLs da API
(/api/...) e o endpoint para obter o token de autenticação.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Painel de administração do Django, onde vais inserir e ver dados reais.
    path("admin/", admin.site.urls),

    # --- A partir do Passo 3, a API vive aqui: ---
    # path("api/", include("fleet.urls")),
    # path("api/", include("equipment.urls")),
    # path("api/", include("alerts.urls")),
    # path("api/auth/token/", obtain_auth_token),  # devolve o token de login
]
