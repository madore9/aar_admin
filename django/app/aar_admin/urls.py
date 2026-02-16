from django.urls import path, include
from django.http import JsonResponse
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('plans.urls.plan_urls')),
    path('batch/', include('plans.urls.batch_urls')),
    path('lookup/', include('plans.urls.lookup_urls')),
    path('course-lists/', include('plans.urls.course_lists_urls')),
    path('set-role/', include('plans.urls.role_urls')),
]
