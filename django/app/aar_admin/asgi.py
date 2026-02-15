"""
ASGI config for AAR Admin project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aar_admin.settings_local')

application = get_asgi_application()
