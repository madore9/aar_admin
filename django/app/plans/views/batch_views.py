import json
from django.shortcuts import render
from django.http import JsonResponse
from plans.services.plan_service import get_plans, get_plan_detail, get_courses
from plans.services.api_client import api_post
from plans.views.plan_views import require_admin


@require_admin
async def batch_add(request):
    plans = await get_plans()
    courses_data = await get_courses()
    context = {
        'active_tab': 'batch',
        'plans': plans,
        'all_courses': courses_data.get('courses', []),
    }
    return render(request, 'batch/batch_add.html', context)


@require_admin
async def api_batch_validate(request):
    """Validate a list of identifiers against the course catalog."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    identifiers = data.get('identifiers', [])
    import_mode = data.get('import_mode', 'catalog')  # 'catalog' or 'id'
    existing_ids = set(data.get('existing_identifiers', []))

    courses_data = await get_courses()
    all_courses = courses_data.get('courses', [])

    results = []
    for raw_input in identifiers:
        raw_input = raw_input.strip()
        if not raw_input:
            continue

        candidates = []
        if import_mode == 'id':
            candidates = [c for c in all_courses if c['system_id'] == raw_input]
        else:
            exact = [c for c in all_courses if c['id'].lower() == raw_input.lower()]
            if exact:
                candidates = exact
            else:
                candidates = [c for c in all_courses if raw_input.lower() in c['id'].lower()]

        if len(candidates) == 1:
            c = candidates[0]
            is_dup = c['system_id'] in existing_ids
            results.append({
                'input': raw_input,
                'status': 'DUPLICATE' if is_dup else 'EXACT_MATCH',
                'candidates': candidates,
                'selected': candidates,
            })
        elif len(candidates) > 1:
            results.append({
                'input': raw_input,
                'status': 'MULTIPLE_MATCHES',
                'candidates': candidates,
                'selected': [],
            })
        else:
            results.append({
                'input': raw_input,
                'status': 'NO_MATCH',
                'candidates': [],
                'selected': [],
            })

    return JsonResponse({'results': results})


async def api_get_plan_requirements(request, plan_id):
    """Get a plan's requirements for the batch add dropdown."""
    plan = await get_plan_detail(plan_id)
    if not plan:
        return JsonResponse({'error': 'Not found'}, status=404)
    reqs = []
    for r in plan.get('requirements', []):
        reqs.append({
            'id': r['id'],
            'title': r['title'],
            'existing_identifiers': [c['identifier'] for c in r.get('courses', [])],
        })
    return JsonResponse({'requirements': reqs, 'plan_name': plan.get('name', '')})
