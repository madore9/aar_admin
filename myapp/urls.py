from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def health(request):
    """Health check endpoint for Docker/nginx."""
    return JsonResponse({"status": "ok"})


def home(request):
    """Home page."""
    return JsonResponse({
        "message": "Welcome to Django on EC2!",
        "app": "myapp",
        "endpoints": {
            "health": "/health/",
            "admin": "/admin/",
        }
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health, name='health'),
    path('', home, name='home'),
]
