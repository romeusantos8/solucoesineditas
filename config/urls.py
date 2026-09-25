"""
Mapa de URLs principal do projeto (o "porteiro" que decide que código corre
para cada endereço).

A API vive toda sob /api/. A autenticação é por JWT:
- POST /api/auth/token/          username+password → { access, refresh }
- POST /api/auth/token/refresh/  { refresh }       → { access } novo
O cliente envia `Authorization: Bearer <access>` nos restantes pedidos. O access
é curto (5 min); quando expira, usa-se o refresh para obter outro sem novo login.
"""

import json
import logging

from axes.helpers import get_lockout_message
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import View
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerSplitView,
)
from rest_framework import status
from rest_framework.response import Response
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
        # Procura o index.html em dois sítios, por esta ordem:
        #  1) STATIC_ROOT — para onde o `collectstatic` copia o build. É o que
        #     sobrevive garantidamente ao runtime em produção (o container que
        #     corre o gunicorn tem os estáticos recolhidos, mas pode não trazer
        #     a pasta frontend/dist original).
        #  2) frontend/dist — o build direto do Vite (caminho em dev local).
        for index in (
            settings.STATIC_ROOT / "index.html",
            settings.FRONTEND_DIST / "index.html",
        ):
            if index.exists():
                return HttpResponse(index.read_bytes())
        return HttpResponse(
            "Build do frontend não encontrado. Corre "
            "<code>npm run build --prefix frontend</code> "
            "(em desenvolvimento usa antes o Vite: "
            "<code>npm run dev --prefix frontend</code>).",
            status=200,
        )

logger_csp = logging.getLogger("config.csp")


@csrf_exempt  # o browser envia o relatório sem token CSRF
@require_POST
def relatorio_csp(request):
    """
    Recebe os relatórios de violação da CSP que os browsers enviam (diretiva
    report-uri, ver POLITICA_CSP em settings) e escreve-os nos logs, que o
    Railway mostra. Assim sabe-se se a CSP bloquearia alguma coisa sem ninguém
    ter de abrir a consola do browser. Público de propósito (o browser não
    envia login); só regista campos curtos, nunca o corpo inteiro.
    """
    try:
        relatorio = json.loads(request.body)["csp-report"]
    except (ValueError, KeyError, TypeError):
        return HttpResponse(status=400)
    if not isinstance(relatorio, dict):
        return HttpResponse(status=400)
    logger_csp.warning(
        "Violação CSP: '%s' bloqueado pela regra '%s' na página %s",
        str(relatorio.get("blocked-uri", ""))[:200],
        str(relatorio.get("violated-directive", ""))[:100],
        str(relatorio.get("document-uri", ""))[:200],
    )
    return HttpResponse(status=204)


# Subclasses só para agrupar estes endpoints na secção "Autenticação" do Swagger.
# São públicos por natureza (login/refresh) — o simplejwt já trata disso.


@extend_schema(tags=["Autenticação"])
class LoginView(TokenObtainPairView):
    """Login: troca username+password por um par de tokens (access + refresh)."""

    def handle_exception(self, exc):
        # O django-axes marca o pedido quando o login fica bloqueado, e o
        # AxesMiddleware transforma essa marca numa resposta 429. Mas aqui a
        # marca fica no objeto Request do DRF, que o middleware não vê: sem
        # isto, um utilizador bloqueado recebia o 401 genérico ("credenciais
        # inválidas") mesmo com a password certa.
        if getattr(self.request, "axes_locked_out", False):
            return Response(
                {"detail": get_lockout_message()},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return super().handle_exception(exc)


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

    # Documentação da API: esquema OpenAPI cru + Swagger UI interativa. A vista
    # "Split" serve o script de arranque num ficheiro à parte (em vez de
    # embutido no HTML), que é o que a CSP permite.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerSplitView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Relatórios de violação da CSP enviados pelos browsers (ver relatorio_csp).
    path("api/csp-report/", relatorio_csp, name="csp-report"),

    # Apanha-tudo: qualquer outra rota devolve a app React (index.html). TEM de
    # ser a ÚLTIMA — só apanha o que não corresponder às rotas acima (api/,
    # admin/, etc.). É o que faz o React Router funcionar com refresh/links diretos.
    re_path(r"^(?!api/|admin/|static/|api-auth/).*$", ReactAppView.as_view()),
]

# Login/logout da Browsable API, só em desenvolvimento. Em produção é mais uma
# porta de login sem necessidade: a sessão do Admin já serve para usar a API
# navegável e a documentação. (Inserido antes do apanha-tudo.)
if settings.DEBUG:
    urlpatterns.insert(-1, path("api-auth/", include("rest_framework.urls")))
