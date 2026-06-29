"""
Definições do Django para o projeto "config".

Lê valores sensíveis e específicos do ambiente a partir do .env (via python-decouple),
em vez de os ter escritos à mão aqui. Assim o mesmo código corre em local e em
produção, e nunca commitamos segredos.

Documentação: https://docs.djangoproject.com/en/5.1/ref/settings/
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
    "rest_framework.authtoken",     # autenticação por Token (a que escolhemos)
    "django_filters",               # filtros de querystring (ex.: ?viatura=ID)
    "corsheaders",                  # permite o frontend React (outro porto) chamar a API
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
    "alerts",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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

# Tipo de chave primária por defeito para os models.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    # Como o utilizador prova quem é. Token para a API (frontend React);
    # Session para conseguires usar a "browsable API" autenticado no browser.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
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
