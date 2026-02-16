from django.urls import path
from plans.views.plan_views import (
    plan_list, plan_detail, api_save_draft, api_discard_draft, api_save_changes,
    api_search_courses, api_get_course_list_detail, api_add_requirement, api_edit_requirement,
    api_get_audit_log, export_plan_csv,
)

urlpatterns = [
    path('', plan_list, name='plan_list'),
    path('plans/<str:plan_id>/', plan_detail, name='plan_detail'),
    path('plans/<str:plan_id>/export/', export_plan_csv, name='export_plan_csv'),
    path('plans/<str:plan_id>/requirements/add/', api_add_requirement, name='add_requirement'),
    path('plans/<str:plan_id>/requirements/<str:req_id>/edit/', api_edit_requirement, name='edit_requirement'),
    path('plans/<str:plan_id>/requirements/<str:req_id>/save-draft/', api_save_draft, name='save_draft'),
    path('plans/<str:plan_id>/requirements/<str:req_id>/discard-draft/', api_discard_draft, name='discard_draft'),
    path('plans/<str:plan_id>/requirements/<str:req_id>/save-changes/', api_save_changes, name='save_changes'),
    path('api/courses/search/', api_search_courses, name='course_search'),
    path('api/course-lists/<str:list_id>/', api_get_course_list_detail, name='course_list_detail'),
    path('api/audit-log/<str:plan_id>/', api_get_audit_log, name='audit_log'),
]
