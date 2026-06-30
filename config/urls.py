"""
Mapa de URLs principal do projeto (o "porteiro" que decide que código corre
para cada endereço).

A API vive toda sob /api/. A autenticação é por JWT:
- POST /api/auth/token/          username+password → { access, refresh }
- POST /api/auth/token/refresh/  { refresh }       → { access } novo
O cliente envia `Authorization: Bearer <access>` nos restantes pedidos. O access
é curto (5 min); quando expira, usa-se o refresh para obter outro sem novo login.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Subclasses só para agrupar estes endpoints na secção "Autenticação" do Swagger.
# São públicos por natureza (login/refresh) — o simplejwt já trata disso.


@extend_schema(tags=["Autenticação"])
class LoginView(TokenObtainPairView):
    """Login: troca username+password por um par de tokens (access + refresh)."""


@extend_schema(tags=["Autenticação"])
class RefreshView(TokenRefreshView):
    """Renova o access token a partir de um refresh token válido."""


urlpatterns = [
    # Painel de administração do Django, onde vais inserir e ver dados reais.
    path("admin/", admin.site.urls),

    # API REST (CRUD de viaturas, equipamentos e tudo o que lhes pertence).
    path("api/", include("fleet.urls")),
    path("api/", include("equipment.urls")),
    path("api/", include("employees.urls")),
    path("api/", include("projects.urls")),

    # Dashboard de alertas: prazos a expirar (GET /api/alerts/?dias=N).
    path("api/", include("alerts.urls")),

    # Autenticação JWT: login (par de tokens) e renovação do access.
    path("api/auth/token/", LoginView.as_view(), name="token-obtain"),
    path("api/auth/token/refresh/", RefreshView.as_view(), name="token-refresh"),

    # Documentação da API: esquema OpenAPI cru + Swagger UI interativa.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Login/logout da Browsable API (para testar autenticado no browser).
    path("api-auth/", include("rest_framework.urls")),
]
