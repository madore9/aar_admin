from django.shortcuts import render
from django.http import JsonResponse
from plans.services.plan_service import get_courses, get_course_usage
from plans.views.plan_views import require_admin


@require_admin
async def course_lookup(request):
    courses_data = await get_courses()
    context = {
        'active_tab': 'lookup',
        'all_courses': courses_data.get('courses', []),
    }
    return render(request, 'lookup/course_lookup.html', context)


@require_admin
async def api_course_usage(request, system_id):
    """AJAX endpoint for course usage lookup."""
    usage = await get_course_usage(system_id)
    return JsonResponse({'usage': usage})
