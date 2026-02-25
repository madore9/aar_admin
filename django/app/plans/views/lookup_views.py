"""
Course lookup views — search and usage analysis.
"""
import logging

from django.http import JsonResponse
from django.shortcuts import render

from plans.services.plan_service import get_courses, get_course_usage
from plans.views.plan_views import require_admin

logger = logging.getLogger(__name__)


@require_admin
async def course_lookup(request):
    courses_data = await get_courses()
    context = {
        'active_tab': 'lookup',
        'all_courses': courses_data.get('courses', []) if courses_data else [],
    }
    return render(request, 'lookup/course_lookup.html', context)


@require_admin
async def api_course_usage(request, system_id):
    """AJAX endpoint for course usage lookup."""
    usage = await get_course_usage(system_id)
    return JsonResponse({'usage': usage})
