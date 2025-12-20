import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET KEY
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-wxis=7n6roizne*%)94#@s7qqz@^8l5180ww44p-&9397z@!k)'
)

# DEBUG: False em produção
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# ALLOWED_HOSTS
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'tipsgolbr.com.br',
    'www.tipsgolbr.com.br',
    'tipsgolbr-django.onrender.com',
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize', 
    
    # Apps do projeto
    'tips_core',
    'widget_tweaks',
]

AUTH_USER_MODEL = 'tips_core.CustomUser'

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tipsgolbr_config.urls'

# TEMPLATES
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tipsgolbr_config.wsgi.application'

# DATABASE
# Desenvolvimento local: SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Produção: PostgreSQL do Render
if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )

# PASSWORDS
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# INTERNACIONALIZAÇÃO
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Só mantenha essa linha se essa pasta realmente EXISTIR
STATICFILES_DIRS = [
    BASE_DIR / 'tips_core/static',
]

# DEFAULT PK
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGIN CONFIG
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'home'

# --- CONFIGURAÇÕES DO PAGSEGURO/PAGBANK ---

# E-MAIL DO VENDEDOR (SUA CONTA PAGSEGURO) - É CRUCIAL!
PAGSEGURO_SELLER_EMAIL = os.environ.get(
    'PAGSEGURO_SELLER_EMAIL',
    'garciainteligencia@hotmail.com' # <--- SUBSTITUA ISTO PELO SEU EMAIL REAL
)

# Token/Chave de integração
PAGSEGURO_TOKEN = os.environ.get(
    'PAGSEGURO_TOKEN', 
    'df0fef46-42d9-473e-b854-ebfd4c588d0deb4b703b405888ace9fe3477b4068d17191a-e8c4-419a-9e2f-34f72bec6803'
)

# Mapeamento dos planos para os detalhes de checkout (valor e código de produto)
PAGSEGURO_PLAN_URLS = {
    1: "https://pag.ae/81fzeG5jm",
    3: "https://pag.ae/81femFKQr",
    6: "https://pag.ae/81fej-om6",
}

# === CONFIGURAÇÕES ADICIONAIS OBRIGATÓRIAS DO PAGSEGURO ===

PAGSEGURO_NOTIFICATION_URL = os.environ.get(
    'PAGSEGURO_NOTIFICATION_URL',
    'https://www.docelarms.com.br/pagseguro/notification/'
)

PAGSEGURO_RETURN_URL = os.environ.get(
    'PAGSEGURO_RETURN_URL',
    'https://www.docelarms.com.br/pagseguro/sucesso/'
)

PAGSEGURO_ENVIRONMENT = os.environ.get(
    'PAGSEGURO_ENVIRONMENT',
    'sandbox'
)