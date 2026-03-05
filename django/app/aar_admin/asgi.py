"""
ASGI config for AAR Admin project.
"""
import os

from django.core.asgi import get_asgi_application

django_env = os.environ.get('DJANGO_ENV', 'local')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'aar_admin.settings_{django_env}')

application = get_asgi_application()
