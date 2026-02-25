"""
Local development settings for AAR Admin.
"""
from .settings import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# Local FastAPI backend
AAR_API_BASE_URL = 'http://localhost:9223'
AAR_API_KEY = 'dev-key-123'
