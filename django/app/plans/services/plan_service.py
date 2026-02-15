from plans.services.api_client import api_get, api_post, api_put, api_delete


async def get_plans(search_query: str = None) -> list[dict]:
    params = {"q": search_query} if search_query else None
    return await api_get("/plans/", params=params) or []


async def get_plan_detail(plan_id: str) -> dict | None:
    return await api_get(f"/plans/{plan_id}")


async def get_courses(query: str = None) -> dict:
    params = {"q": query} if query else None
    return await api_get("/courses/", params=params) or {"courses": [], "total": 0}


async def get_course_usage(system_id: str) -> list[dict]:
    return await api_get(f"/courses/{system_id}/usage") or []


async def get_course_lists() -> list[dict]:
    return await api_get("/course-lists/") or []


async def get_course_list_detail(list_id: str) -> dict | None:
    return await api_get(f"/course-lists/{list_id}")


async def save_changes(plan_id: str, req_id: str, changes: dict) -> dict | None:
    return await api_post(f"/plans/{plan_id}/requirements/{req_id}/save-changes", changes)


async def add_requirement(plan_id: str, data: dict) -> dict | None:
    return await api_post(f"/plans/{plan_id}/requirements", data)


async def edit_requirement(plan_id: str, req_id: str, data: dict) -> dict | None:
    return await api_put(f"/plans/{plan_id}/requirements/{req_id}", data)


async def save_draft(plan_id: str, req_id: str, changes_json: dict) -> dict | None:
    return await api_post(f"/plans/{plan_id}/requirements/{req_id}/drafts", {"changes_json": changes_json})


async def delete_draft(plan_id: str, req_id: str) -> bool:
    return await api_delete(f"/plans/{plan_id}/requirements/{req_id}/drafts")


async def get_drafts(plan_id: str) -> list[dict]:
    return await api_get(f"/plans/{plan_id}/drafts") or []


async def create_audit_entry(plan_id: str, user: str, action: str) -> dict | None:
    return await api_post("/audit-log/", {"plan_id": plan_id, "user": user, "action": action})


async def get_audit_log(plan_id: str) -> list[dict]:
    return await api_get(f"/audit-log/{plan_id}") or []


async def get_plan_with_course_info(plan_id: str) -> dict | None:
    """Get plan and enrich requirement courses with catalog info."""
    plan = await get_plan_detail(plan_id)
    if not plan:
        return None
    courses_data = await get_courses()
    courses = courses_data.get('courses', [])
    course_map = {c['system_id']: c for c in courses}
    for req in plan.get('requirements', []):
        for rc in req.get('courses', []):
            rc['course_info'] = course_map.get(rc['identifier'], {})
    return plan
