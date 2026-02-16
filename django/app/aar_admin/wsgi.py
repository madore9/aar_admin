"""
WSGI config for AAR Admin project.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aar_admin.settings_local')

application = get_wsgi_application()
