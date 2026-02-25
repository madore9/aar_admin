"""
Production settings for AAR Admin.
"""
import os
from .settings import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # Required in production

# Production FastAPI backend
AAR_API_BASE_URL = os.environ.get('AAR_API_BASE_URL', 'http://localhost:9223')

# CSRF — trust nginx reverse proxy
CSRF_TRUSTED_ORIGINS = [
    'https://aar-admin.my.harvard.edu',
]

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Co-tenancy prefix
FORCE_SCRIPT_NAME = '/aar-admin'

# Static file versioning
STORAGES = {
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage',
    },
}

# --- Redis cache (matches myharvard production pattern, SSL via rediss://) --
# In production, AAR_REDIS_URL should be set to rediss://... (TLS required on ElastiCache)
_REDIS_URL = os.environ.get('AAR_REDIS_URL', 'redis://localhost:6379')
_REDIS_OPTS = {
    'retry_on_timeout': True,
    'socket_keepalive': True,
    'max_connections': 20,
    'socket_connect_timeout': 5,
    'socket_timeout': 5,
    'health_check_interval': 30,
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': _REDIS_URL,
        'OPTIONS': _REDIS_OPTS,
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': _REDIS_URL,
        'KEY_PREFIX': 'SESSIONS',
        'OPTIONS': _REDIS_OPTS,
    },
}
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_SAVE_EVERY_REQUEST = True
AAR_CACHE_ENABLED = True
