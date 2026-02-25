"""
Context processors for AAR Admin.

Mirrors my.harvard pattern: user_role + environment_variables injected
into every template context.
"""
from django.conf import settings


def user_role(request):
    """Inject current user role from session."""
    return {'user_role': request.session.get('user_role', 'DEPT_USER')}


def environment_variables(request):
    """Inject app metadata and environment info into templates."""
    return {
        'APP_VERSION': getattr(settings, 'APP_VERSION', 'local'),
        'APP_ENV': getattr(settings, 'APP_ENV', 'local'),
        'APP_NAME': getattr(settings, 'APP_NAME', 'AAR Admin'),
    }
