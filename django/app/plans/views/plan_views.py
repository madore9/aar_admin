import csv
import io
import json
from functools import wraps
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST
from plans.services.plan_service import (
    get_plans, get_plan_with_course_info, get_courses, get_course_lists,
    get_course_list_detail, add_requirement, edit_requirement,
)
from plans.services.api_client import api_get, api_post, api_delete


def require_admin(view_func):
    """Decorator that returns 403 if user is not ADMIN_USER."""
    @wraps(view_func)
    async def wrapper(request, *args, **kwargs):
        if request.session.get('user_role', 'DEPT_USER') != 'ADMIN_USER':
            return JsonResponse({'error': 'Admin access required'}, status=403)
        return await view_func(request, *args, **kwargs)
    return wrapper


def _build_audit_action(action_type, **kwargs):
    """Build standardized audit action strings matching prototype format."""
    if action_type == 'add_requirement':
        return f"Added new requirement: '{kwargs.get('title', 'Unknown')}'."
    elif action_type == 'edit_requirement':
        title = kwargs.get('title', 'Unknown')
        changes = kwargs.get('changes', {})
        if changes:
            parts = [f"{k} to '{v}'" for k, v in changes.items()]
            return f"Edited requirement '{title}': changed {', '.join(parts)}."
        return f"Edited requirement '{title}'."
    elif action_type == 'save_changes':
        title = kwargs.get('req_title', 'Unknown')
        scope = kwargs.get('scope', '')
        data = kwargs.get('data', {})
        parts = []
        additions = data.get('additions', [])
        removals = data.get('removals', [])
        modifications = data.get('modifications', [])
        if additions:
            parts.append(f"Added: {', '.join(str(a.get('identifier', a)) if isinstance(a, dict) else str(a) for a in additions)}")
        if removals:
            parts.append(f"Removed: {', '.join(str(r) for r in removals)}")
        if modifications:
            mod_strs = []
            for m in modifications:
                if isinstance(m, dict):
                    mod_strs.append(f"{m.get('identifier', '?')} ({m.get('change_type', 'modified')})")
                else:
                    mod_strs.append(str(m))
            parts.append(f"Modified: {', '.join(mod_strs)}")
        scope_str = f" (Scope: {scope})" if scope else ""
        changes_str = '; '.join(parts) if parts else 'No changes'
        return f"Updated requirement '{title}'{scope_str}: {changes_str}."
    return action_type


async def plan_list(request):
    search_query = request.GET.get('q', '')
    plans = await get_plans(search_query if search_query else None)
    context = {
        'plans': plans,
        'search_query': search_query,
        'active_tab': 'plans',
    }
    return render(request, 'plans/plan_list.html', context)


async def plan_detail(request, plan_id):
    plan = await get_plan_with_course_info(plan_id)
    if not plan:
        raise Http404("Plan not found")
    courses_data = await get_courses()
    course_lists = await get_course_lists()
    context = {
        'plan': plan,
        'all_courses': courses_data.get('courses', []),
        'course_lists': course_lists,
        'active_tab': 'plans',
    }
    return render(request, 'plans/plan_detail.html', context)


@require_POST
async def set_role(request):
    role = request.POST.get('role', 'DEPT_USER')
    if role in ('ADMIN_USER', 'DEPT_USER'):
        request.session['user_role'] = role
    return JsonResponse({'role': role})


async def api_search_courses(request):
    """AJAX endpoint for course search autocomplete."""
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'courses': []})
    courses_data = await get_courses(q)
    return JsonResponse(courses_data)


async def api_get_course_list_detail(request, list_id):
    """AJAX endpoint to get course list with its courses."""
    result = await get_course_list_detail(list_id)
    if not result:
        return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse(result)


@require_admin
async def api_add_requirement(request, plan_id):
    """Add a new requirement to a plan."""
    if request.method == 'POST':
        data = json.loads(request.body)
        result = await add_requirement(plan_id, data)
        if result:
            user_role = request.session.get('user_role', 'DEPT_USER')
            await api_post("/audit-log/", {
                "plan_id": plan_id,
                "user": user_role,
                "action": _build_audit_action('add_requirement', title=data.get('title', 'Unknown'))
            })
            return JsonResponse({'status': 'ok', 'requirement': result})
        return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@require_admin
async def api_edit_requirement(request, plan_id, req_id):
    """Edit an existing requirement's metadata."""
    if request.method == 'POST':
        data = json.loads(request.body)
        result = await edit_requirement(plan_id, req_id, data)
        if result:
            user_role = request.session.get('user_role', 'DEPT_USER')
            await api_post("/audit-log/", {
                "plan_id": plan_id,
                "user": user_role,
                "action": _build_audit_action('edit_requirement', title=data.get('title', req_id), changes=data)
            })
            return JsonResponse({'status': 'ok', 'requirement': result})
        return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@require_admin
async def api_save_draft(request, plan_id, req_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = await api_post(f"/plans/{plan_id}/requirements/{req_id}/drafts", {"changes_json": data})
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@require_admin
async def api_discard_draft(request, plan_id, req_id):
    if request.method == 'POST':
        await api_delete(f"/plans/{plan_id}/requirements/{req_id}/drafts")
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@require_admin
async def api_save_changes(request, plan_id, req_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = await api_post(f"/plans/{plan_id}/requirements/{req_id}/save-changes", data)
        if result:
            user_role = request.session.get('user_role', 'DEPT_USER')
            scope = data.get('scope', '')
            await api_post("/audit-log/", {
                "plan_id": plan_id,
                "user": user_role,
                "action": _build_audit_action('save_changes', req_title=req_id, scope=scope, data=data)
            })
            return JsonResponse({'status': 'ok', 'requirement': result})
        return JsonResponse({'status': 'error'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


async def api_get_audit_log(request, plan_id):
    """Get audit log entries for a plan."""
    result = await api_get(f"/audit-log/{plan_id}")
    return JsonResponse({'entries': result or []})


async def export_plan_csv(request, plan_id):
    """Export plan requirements and courses as CSV."""
    from plans.services.plan_service import get_plan_with_course_info
    plan = await get_plan_with_course_info(plan_id)
    if not plan:
        raise Http404("Plan not found")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Plan Name', 'Plan Type', 'Requirement Title', 'Description',
                     'Subject/Catalog', 'Course ID', 'Course Title', 'Department', 'Credits'])

    for req in plan.get('requirements', []):
        for course in req.get('courses', []):
            info = course.get('course_info', {})
            is_wildcard = course.get('is_wildcard', False)
            writer.writerow([
                plan.get('name', ''),
                plan.get('type', ''),
                req.get('title', ''),
                req.get('description', ''),
                info.get('id', course.get('identifier', '')),
                course.get('identifier', ''),
                'WILDCARD' if is_wildcard else info.get('title', ''),
                info.get('department', ''),
                info.get('credits', ''),
            ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    safe_name = plan.get('name', 'plan').replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}_Requirements.csv"'
    return response
