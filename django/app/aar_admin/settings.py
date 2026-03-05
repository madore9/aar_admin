"""
Django settings for AAR Admin project — shared base.

Environment-specific overrides live in settings_local.py, settings_dev.py, etc.
Active settings file is selected via DJANGO_ENV env var (default: local).
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Security -----------------------------------------------------------
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-aar-admin-dev-key-change-in-production',
)

DEBUG = False  # Overridden per-environment

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',') or []

# --- Application ---------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'plans',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'aar_admin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / '_templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'aar_admin.context_processors.user_role',
                'aar_admin.context_processors.environment_variables',
            ],
            'builtins': [
                'django.templatetags.static',
            ],
        },
    },
]

ASGI_APPLICATION = 'aar_admin.asgi.application'
WSGI_APPLICATION = 'aar_admin.wsgi.application'

# --- Database ------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- Internationalization ------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

# --- Static files --------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- AAR API (FastAPI backend) -------------------------------------------
AAR_API_BASE_URL = os.environ.get('AAR_API_BASE_URL', 'http://localhost:9223')
AAR_API_KEY = os.environ.get('AAR_API_KEY', 'dev-key-123')

# --- Cache (LocMemCache is the safe default — no Redis server required) --
# Overridden in settings_dev.py / settings_prod.py with Redis backends.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}

# Feature flags — disabled locally; dev/prod enable via settings override
AAR_CACHE_ENABLED = False
AAR_CACHE_TTL = 3600  # 1 hour default, override per-use

# --- Sessions (cookie-based to avoid DB hits in async views) -------------
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# --- App metadata --------------------------------------------------------
APP_VERSION = os.environ.get('APP_VERSION', 'local')
APP_ENV = os.environ.get('DJANGO_ENV', 'local')
APP_NAME = 'AAR Admin'

# --- Logging (matches my.harvard production format) ----------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} loglevel={levelname:<6s} logger={name} {funcName}() L{lineno:<4d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'aar_admin': {'level': 'DEBUG', 'propagate': True},
        'plans': {'level': 'DEBUG', 'propagate': True},
    },
}
