"""
Dev environment settings for AAR Admin (EC2 Docker deployment).
"""
import os
from .settings import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Dev FastAPI backend
AAR_API_BASE_URL = os.environ.get('AAR_API_BASE_URL', 'http://localhost:9223')

# CSRF — trust nginx reverse proxy
CSRF_TRUSTED_ORIGINS = [
    'https://aar-admin-dev.my.harvard.edu',
]

# Co-tenancy prefix
FORCE_SCRIPT_NAME = '/aar-admin'

# --- Redis cache (matches myharvard production pattern) ------------------
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
