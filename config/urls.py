"""
Mapa de URLs principal do projeto (o "porteiro" que decide que código corre
para cada endereço).

A API vive toda sob /api/. A autenticação é por JWT:
- POST /api/auth/token/          username+password → { access, refresh }
- POST /api/auth/token/refresh/  { refresh }       → { access } novo
O cliente envia `Authorization: Bearer <access>` nos restantes pedidos. O access
é curto (5 min); quando expira, usa-se o refresh para obter outro sem novo login.
"""

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.generic import View
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


class ReactAppView(View):
    """
    Serve o index.html do build do React para qualquer rota que não seja da API.
    O React Router trata da navegação no cliente; assim, dar refresh numa página
    interna (ex.: /obras/3) devolve a app em vez de 404. Em dev (sem build) dá
    uma mensagem a explicar como gerar o build.
    """

    def get(self, request, *args, **kwargs):
        index = settings.FRONTEND_DIST / "index.html"
        if index.exists():
            return HttpResponse(index.read_bytes())
        return HttpResponse(
            "Build do frontend não encontrado. Corre "
            "<code>npm run build --prefix frontend</code> "
            "(em desenvolvimento usa antes o Vite: "
            "<code>npm run dev --prefix frontend</code>).",
            status=200,
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
    path("api/", include("health_records.urls")),

    # Dashboard de alertas: prazos a expirar (GET /api/alerts/?dias=N).
    path("api/", include("alerts.urls")),

    # Relatórios (agregações de despesas por mês).
    path("api/", include("reports.urls")),

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

    # Apanha-tudo: qualquer outra rota devolve a app React (index.html). TEM de
    # ser a ÚLTIMA — só apanha o que não corresponder às rotas acima (api/,
    # admin/, etc.). É o que faz o React Router funcionar com refresh/links diretos.
    re_path(r"^(?!api/|admin/|static/|api-auth/).*$", ReactAppView.as_view()),
]
