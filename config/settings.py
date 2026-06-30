"""
Definições do Django para o projeto "config".

Lê valores sensíveis e específicos do ambiente a partir do .env (via python-decouple),
em vez de os ter escritos à mão aqui. Assim o mesmo código corre em local e em
produção, e nunca commitamos segredos.

Documentação: https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from pathlib import Path

from decouple import Csv, config

# BASE_DIR é a raiz do projeto (a pasta que contém o manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Segurança / ambiente (lidos do .env)
# ---------------------------------------------------------------------------

# config("NOME") lê a variável do .env. Se faltar, o arranque falha com um erro
# claro — o que é bom: obriga-nos a configurar tudo de propósito.
SECRET_KEY = config("SECRET_KEY")

# cast=bool converte a string "True"/"False" do .env num booleano de Python.
DEBUG = config("DEBUG", default=False, cast=bool)

# Csv() transforma "127.0.0.1,localhost" numa lista ['127.0.0.1', 'localhost'].
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

# Origens (frontend) autorizadas a chamar a API. O React em dev corre no Vite
# (http://localhost:5173). Em produção, acrescenta aqui o domínio do site.
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)


# ---------------------------------------------------------------------------
# Aplicações instaladas
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",          # sistema de utilizadores, grupos e permissões
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",               # Django REST Framework
    "rest_framework_simplejwt",     # autenticação por JWT (access curto + refresh)
    "django_filters",               # filtros de querystring (ex.: ?viatura=ID)
    "corsheaders",                  # permite o frontend React (outro porto) chamar a API
    "drf_spectacular",              # gera o esquema OpenAPI / Swagger UI da API
]

# As nossas apps de domínio. Cada uma tem uma responsabilidade clara:
#  - accounts:  login / utilizadores (separado da lógica de negócio)
#  - fleet:     viaturas e tudo o que lhes pertence
#  - equipment: equipamentos e certificados
#  - alerts:    dashboard de prazos a expirar (só lê as outras apps)
LOCAL_APPS = [
    "accounts",
    "fleet",
    "equipment",
    "employees",
    "projects",
    "alerts",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serve os ficheiros estáticos (CSS/JS do Admin) em produção, sem
    # precisar de um servidor web à frente. Vem logo a seguir ao SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # CORS tem de vir o mais cedo possível, antes do CommonMiddleware, para
    # conseguir adicionar os cabeçalhos certos às respostas.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Base de dados — PostgreSQL (credenciais vêm do .env)
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", default="127.0.0.1"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}


# ---------------------------------------------------------------------------
# Validação de passwords
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internacionalização — empresa em Portugal / região UE
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Europe/Lisbon"
USE_I18N = True
USE_TZ = True  # guarda datas/horas em UTC na BD; boa prática.


# ---------------------------------------------------------------------------
# Ficheiros estáticos
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: comprime e adiciona hash ao nome dos ficheiros (cache eterna no
# browser, invalidada quando o conteúdo muda). Usado depois de `collectstatic`.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Tipo de chave primária por defeito para os models.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Segurança em produção (só ativa quando DEBUG=False)
# ---------------------------------------------------------------------------
# Em desenvolvimento (DEBUG=True) estes ficam desligados para não atrapalhar o
# trabalho local em http. Em produção, o README promete HTTPS e há dados RGPD,
# por isso forçamos ligação cifrada e cookies seguros.

if not DEBUG:
    # Redireciona qualquer http:// para https://.
    SECURE_SSL_REDIRECT = True
    # Os cookies de sessão e CSRF só viajam por HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS: o browser passa a recusar http durante este período (1 ano).
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Confia no cabeçalho do proxy (Railway/Render) para saber que o pedido
    # original era HTTPS.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Origens de confiança para CSRF (o domínio do site). Lê do .env em produção.
    CSRF_TRUSTED_ORIGINS = config(
        "CSRF_TRUSTED_ORIGINS", default="", cast=Csv()
    )


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    # Como o utilizador prova quem é. JWT para a API (frontend React);
    # Session para conseguires usar a "browsable API" autenticado no browser.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    # Regra global: por defeito, é preciso estar autenticado para usar a API.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Filtros de querystring por defeito (django-filter). Cada ViewSet declara
    # depois que campos aceita filtrar via `filterset_fields`.
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    # Paginação: listas vêm em páginas de 50 para não devolver tudo de uma vez.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    # drf-spectacular gera o esquema OpenAPI a partir dos serializers/views.
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # ----------------------------------------------------------------------
    # GANCHO PARA O FUTURO (roles/permissões) — NÃO ativar agora.
    # Quando quiseres permissões por papel, o caminho típico é:
    #   1) criar Django Groups (ex.: "Gestor de Frota", "Leitor") no Admin;
    #   2) atribuir permissões a esses grupos;
    #   3) trocar a permissão acima por "DjangoModelPermissions" (ou uma classe
    #      de permissão própria) para que o DRF respeite essas permissões.
    # Deixamos a porta aberta; o sistema completo fica para outra fase.
    # ----------------------------------------------------------------------
}


# ---------------------------------------------------------------------------
# drf-spectacular — documentação OpenAPI / Swagger
# ---------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "API Gestão de Recursos",
    "DESCRIPTION": "Gestão de viaturas, equipamentos e alertas de prazos.",
    "VERSION": "1.0.0",
    # Não serve o esquema cru na própria UI (a UI já o vai buscar à rota dedicada).
    "SERVE_INCLUDE_SCHEMA": False,
    # Faz o botão "Authorize" do Swagger UI lembrar-se do token entre pedidos.
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}
# Nota: com JWT, no Swagger UI clica em "Authorize" e escreve
#   Bearer <access-token>  (a palavra Bearer, espaço, o token de /api/auth/token/).


# ---------------------------------------------------------------------------
# Simple JWT — tempos de vida dos tokens
# ---------------------------------------------------------------------------
# Access curto (5 min): se for roubado, expira depressa. Refresh mais longo
# (1 dia) renova o access sem novo login. ROTATE + BLACKLIST não são usados aqui
# (exigiriam a app de blacklist e BD); o refresh curto já dá boa margem.

from datetime import timedelta  # noqa: E402  (perto do uso, de propósito)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}
