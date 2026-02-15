from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from plans.views.plan_views import require_admin
import httpx


AAR_API_URL = "http://localhost:9223"


@require_admin
async def course_lists(request):
    """Display all course lists."""
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            response = await client.get("/aar/course-lists/")
            response.raise_for_status()
            course_lists = response.json()
        except Exception:
            course_lists = []

    context = {
        "active_tab": "course-lists",
        "course_lists": course_lists,
    }
    return render(request, "course_lists/course_lists.html", context)


@require_admin
async def course_list_detail(request, list_id):
    """Display single course list with courses and usage."""
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            # Get list details
            list_response = await client.get(f"/aar/course-lists/{list_id}")
            list_response.raise_for_status()
            course_list = list_response.json()
        except Exception:
            course_list = None

        try:
            # Get usage
            usage_response = await client.get(f"/aar/course-lists/{list_id}/usage")
            usage = usage_response.json().get("usage", [])
        except Exception:
            usage = []

        try:
            # Get all courses for autocomplete
            courses_response = await client.get("/aar/courses/")
            all_courses = courses_response.json().get("courses", [])
        except Exception:
            all_courses = []

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
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            response = await client.post(
                "/aar/course-lists/",
                json={"name": name, "description": description}
            )
            response.raise_for_status()
            return JsonResponse(response.json(), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["PUT"])
async def api_update_course_list(request, list_id):
    """API: Update a course list."""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()

    if not name:
        return JsonResponse({"error": "Name is required"}, status=400)

    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            response = await client.put(
                f"/aar/course-lists/{list_id}",
                json={"name": name, "description": description}
            )
            response.raise_for_status()
            return JsonResponse(response.json())
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["DELETE"])
async def api_delete_course_list(request, list_id):
    """API: Delete a course list."""
    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            response = await client.delete(f"/aar/course-lists/{list_id}")
            response.raise_for_status()
            return JsonResponse({"message": "Deleted"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
async def api_add_courses_to_list(request, list_id):
    """API: Add courses to a course list."""
    import json
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    courses = data.get("courses", [])

    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            response = await client.post(
                f"/aar/course-lists/{list_id}/courses",
                json={"courses": courses}
            )
            response.raise_for_status()
            return JsonResponse(response.json())
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["DELETE"])
async def api_remove_course_from_list(request, list_id, identifier):
    """API: Remove a course from a course list."""
    # URL decode the identifier
    import urllib.parse
    identifier = urllib.parse.unquote(identifier)

    async with httpx.AsyncClient(base_url=AAR_API_URL, timeout=10.0) as client:
        try:
            response = await client.delete(
                f"/aar/course-lists/{list_id}/courses/{identifier}"
            )
            response.raise_for_status()
            return JsonResponse({"message": "Removed"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
