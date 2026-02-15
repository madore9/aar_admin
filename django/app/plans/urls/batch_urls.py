from django.urls import path
from plans.views.batch_views import batch_add, api_batch_validate, api_get_plan_requirements

urlpatterns = [
    path('', batch_add, name='batch_add'),
    path('api/batch/validate/', api_batch_validate, name='batch_validate'),
    path('api/batch/plan/<str:plan_id>/requirements/', api_get_plan_requirements, name='plan_requirements'),
]
