from django.urls import path
from plans.views.plan_views import set_role

urlpatterns = [
    path('', set_role, name='set_role'),
]
