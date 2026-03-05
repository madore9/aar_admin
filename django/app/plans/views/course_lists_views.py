"""
Course Lists views — CRUD operations for shared course lists.
"""
import asyncio
import json
import logging
import urllib.parse

from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from aar_admin.common.aar_api import api_get, api_post, api_put, api_delete
from plans.views.plan_views import require_admin

logger = logging.getLogger(__name__)


@require_admin
async def course_lists(request):
    """Display all course lists."""
    all_lists = await api_get("/course-lists/") or []

    context = {
        "active_tab": "course-lists",
        "course_lists": all_lists,
    }
    return render(request, "course_lists/course_lists.html", context)


@require_admin
async def course_list_detail(request, list_id):
    """Display single course list with courses and usage."""
    course_list, usage_data, courses_data = await asyncio.gather(
        api_get(f"/course-lists/{list_id}"),
        api_get(f"/course-lists/{list_id}/usage"),
        api_get("/courses/"),
    )

    if not course_list:
        raise Http404("Course list not found")

    usage = usage_data.get("usage", []) if usage_data else []
    all_courses = courses_data.get("courses", []) if courses_data else []

    context = {
        "active_tab": "course-lists",
        "course_list": course_list,
        "usage": usage,
        "all_courses": all_courses,
    }
    return render(request, "course_lists/course_list_detail.html", context)


@require_http_methods(["POST"])
async def api_create_course_list(request):
    """API: Create a new course list."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    result = await api_post("/course-lists/", {"name": name, "description": description})
    if result is None:
        logger.error(f"Failed to create course list: {name}")
        return JsonResponse({"error": "Failed to create course list"}, status=502)
    return JsonResponse(result, status=201)


@require_http_methods(["PUT"])
async def api_update_course_list(request, list_id):
    """API: Update a course list."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    result = await api_put(f"/course-lists/{list_id}", {"name": name, "description": description})
    if result is None:
        logger.error(f"Failed to update course list: {list_id}")
        return JsonResponse({"error": "Failed to update course list"}, status=502)
    return JsonResponse(result)


@require_http_methods(["DELETE"])
async def api_delete_course_list(request, list_id):
    """API: Delete a course list."""
    success = await api_delete(f"/course-lists/{list_id}")
    if not success:
        logger.error(f"Failed to delete course list: {list_id}")
        return JsonResponse({"error": "Failed to delete course list"}, status=502)
    return JsonResponse({"message": "Deleted"})


@require_http_methods(["POST"])
async def api_add_courses_to_list(request, list_id):
    """API: Add courses to a course list."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    courses = data.get("courses", [])
    result = await api_post(f"/course-lists/{list_id}/courses", {"courses": courses})
    if result is None:
        logger.error(f"Failed to add courses to list: {list_id}")
        return JsonResponse({"error": "Failed to add courses"}, status=502)
    return JsonResponse(result)


@require_http_methods(["DELETE"])
async def api_remove_course_from_list(request, list_id, identifier):
    """API: Remove a course from a course list."""
    identifier = urllib.parse.unquote(identifier)
    success = await api_delete(f"/course-lists/{list_id}/courses/{identifier}")
    if not success:
        logger.error(f"Failed to remove course {identifier} from list {list_id}")
        return JsonResponse({"error": "Failed to remove course"}, status=502)
    return JsonResponse({"message": "Removed"})
