from django.urls import path
from plans.views.lookup_views import course_lookup, api_course_usage

urlpatterns = [
    path('', course_lookup, name='course_lookup'),
    path('api/courses/<str:system_id>/usage/', api_course_usage, name='course_usage'),
]
