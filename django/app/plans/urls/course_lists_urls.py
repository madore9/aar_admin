from django.urls import path
from plans.views import course_lists_views

urlpatterns = [
    path('', course_lists_views.course_lists, name='course_lists'),
    path('<str:list_id>/', course_lists_views.course_list_detail, name='course_list_detail'),
    path('api/create/', course_lists_views.api_create_course_list, name='api_create_course_list'),
    path('api/<str:list_id>/update/', course_lists_views.api_update_course_list, name='api_update_course_list'),
    path('api/<str:list_id>/delete/', course_lists_views.api_delete_course_list, name='api_delete_course_list'),
    path('api/<str:list_id>/courses/add/', course_lists_views.api_add_courses_to_list, name='api_add_courses_to_list'),
    path('api/<str:list_id>/courses/<str:identifier>/remove/', course_lists_views.api_remove_course_from_list, name='api_remove_course_from_list'),
]
