import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.databases.sqlite_db import execute_query, execute_write
from app.schemas.plan import (
    AcademicPlan, PlanType, Requirement, RequirementCourse,
    AddRequirementRequest, EditRequirementRequest, SaveChangesRequest,
)

router = APIRouter(prefix="/plans", tags=["plans"])


def _parse_valid_terms(raw):
    """Parse valid_terms from JSON string stored in SQLite."""
    if raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _build_requirement_course(row: dict) -> RequirementCourse:
    """Build a RequirementCourse from a DB row."""
    return RequirementCourse(
        identifier=row["identifier"],
        is_wildcard=bool(row["is_wildcard"]),
        is_excluded=bool(row.get("is_excluded", 0)),
        include_equivalent_courses=bool(row.get("include_equivalent_courses", 0)),
        validity_type=row.get("validity_type", "ALWAYS"),
        valid_terms=_parse_valid_terms(row.get("valid_terms")),
        valid_from=row.get("valid_from"),
        valid_to=row.get("valid_to"),
    )


def _build_requirement(row: dict, courses: list[RequirementCourse]) -> Requirement:
    """Build a Requirement from a DB row + courses."""
    return Requirement(
        id=row["id"],
        title=row["title"],
        description=row.get("description", ""),
        required_courses_count=row.get("required_courses_count", 0),
        required_units=row.get("required_units", 0),
        minimum_gpa=row.get("minimum_gpa"),
        courses=courses,
        course_list_id=row.get("course_list_id"),
    )


async def _get_requirement_with_courses(req_id: str) -> Requirement:
    """Get a requirement with its courses."""
    req_data = await execute_query(
        "SELECT * FROM requirements WHERE id = ?", [req_id], fetch_one=True
    )
    if not req_data:
        raise HTTPException(status_code=404, detail="Requirement not found")

    courses_data = await execute_query(
        "SELECT * FROM requirement_courses WHERE requirement_id = ?", [req_id]
    )
    courses = [_build_requirement_course(c) for c in courses_data]
    return _build_requirement(req_data, courses)


@router.get("/")
async def list_plans(q: str = None):
    """List all plans (without nested requirements)."""
    if q:
        plans_data = await execute_query(
            "SELECT * FROM academic_plans WHERE name LIKE ? OR type LIKE ? ORDER BY name",
            [f"%{q}%", f"%{q}%"]
        )
    else:
        plans_data = await execute_query("SELECT * FROM academic_plans ORDER BY name")

    return [
        AcademicPlan(
            id=p["id"], name=p["name"], type=PlanType(p["type"]),
            last_updated=p["last_updated"], requirements=[]
        )
        for p in plans_data
    ]


@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    """Get a plan with nested requirements and courses."""
    plan_data = await execute_query(
        "SELECT * FROM academic_plans WHERE id = ?", [plan_id], fetch_one=True
    )
    if not plan_data:
        raise HTTPException(status_code=404, detail="Plan not found")

    reqs_data = await execute_query(
        "SELECT * FROM requirements WHERE plan_id = ? ORDER BY sort_order", [plan_id]
    )

    requirements = []
    for req in reqs_data:
        courses_data = await execute_query(
            "SELECT * FROM requirement_courses WHERE requirement_id = ?", [req["id"]]
        )
        courses = [_build_requirement_course(c) for c in courses_data]
        requirements.append(_build_requirement(req, courses))

    return AcademicPlan(
        id=plan_data["id"], name=plan_data["name"],
        type=PlanType(plan_data["type"]), last_updated=plan_data["last_updated"],
        requirements=requirements
    )


@router.post("/{plan_id}/requirements", status_code=status.HTTP_201_CREATED)
async def add_requirement(plan_id: str, request: AddRequirementRequest):
    """Add a new requirement to a plan."""
    plan = await execute_query(
        "SELECT * FROM academic_plans WHERE id = ?", [plan_id], fetch_one=True
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    max_order = await execute_query(
        "SELECT MAX(sort_order) as max_order FROM requirements WHERE plan_id = ?",
        [plan_id], fetch_one=True
    )
    new_sort_order = (max_order["max_order"] or 0) + 1

    req_id = str(uuid.uuid4())
    await execute_write(
        "INSERT INTO requirements (id, plan_id, title, description, required_courses_count, required_units, minimum_gpa, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [req_id, plan_id, request.title, request.description,
         request.required_courses_count, request.required_units, request.minimum_gpa, new_sort_order]
    )

    await execute_write(
        "UPDATE academic_plans SET last_updated = ? WHERE id = ?",
        [datetime.now(timezone.utc).isoformat(), plan_id]
    )

    return await _get_requirement_with_courses(req_id)


@router.put("/{plan_id}/requirements/{req_id}")
async def edit_requirement(plan_id: str, req_id: str, request: EditRequirementRequest):
    """Edit requirement metadata (only non-None fields)."""
    req = await execute_query(
        "SELECT * FROM requirements WHERE id = ? AND plan_id = ?",
        [req_id, plan_id], fetch_one=True
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    updates = []
    params = []
    for field, col in [
        ("title", "title"), ("description", "description"),
        ("required_courses_count", "required_courses_count"),
        ("required_units", "required_units"), ("minimum_gpa", "minimum_gpa"),
    ]:
        val = getattr(request, field)
        if val is not None:
            updates.append(f"{col} = ?")
            params.append(val)

    if updates:
        params.append(req_id)
        await execute_write(
            f"UPDATE requirements SET {', '.join(updates)} WHERE id = ?", params
        )
        await execute_write(
            "UPDATE academic_plans SET last_updated = ? WHERE id = ?",
            [datetime.now(timezone.utc).isoformat(), plan_id]
        )

    return await _get_requirement_with_courses(req_id)


@router.post("/{plan_id}/requirements/{req_id}/save-changes")
async def save_changes(plan_id: str, req_id: str, request: SaveChangesRequest):
    """Apply pending changes (additions, removals, modifications)."""
    req = await execute_query(
        "SELECT * FROM requirements WHERE id = ? AND plan_id = ?",
        [req_id, plan_id], fetch_one=True
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    changes = request.changes

    # Additions: dict[identifier, RequirementCourse]
    for identifier, course in changes.additions.items():
        await execute_write(
            "INSERT OR REPLACE INTO requirement_courses (requirement_id, identifier, is_wildcard, is_excluded, include_equivalent_courses, validity_type, valid_terms, valid_from, valid_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [req_id, course.identifier, int(course.is_wildcard),
             int(course.is_excluded or False), int(course.include_equivalent_courses or False),
             course.validity_type,
             json.dumps(course.valid_terms) if course.valid_terms else None,
             course.valid_from, course.valid_to]
        )

    # Removals: list[identifier]
    for identifier in changes.removals:
        await execute_write(
            "DELETE FROM requirement_courses WHERE requirement_id = ? AND identifier = ?",
            [req_id, identifier]
        )

    # Modifications: dict[identifier, partial fields]
    for identifier, mods in changes.modifications.items():
        existing = await execute_query(
            "SELECT * FROM requirement_courses WHERE requirement_id = ? AND identifier = ?",
            [req_id, identifier], fetch_one=True
        )
        if existing:
            update_parts = []
            update_params = []
            for key, val in mods.items():
                if key == "valid_terms":
                    update_parts.append("valid_terms = ?")
                    update_params.append(json.dumps(val) if val else None)
                elif key in ("is_excluded", "include_equivalent_courses", "is_wildcard"):
                    update_parts.append(f"{key} = ?")
                    update_params.append(int(val))
                else:
                    update_parts.append(f"{key} = ?")
                    update_params.append(val)
            if update_parts:
                update_params.extend([req_id, identifier])
                await execute_write(
                    f"UPDATE requirement_courses SET {', '.join(update_parts)} WHERE requirement_id = ? AND identifier = ?",
                    update_params
                )

    # Update plan timestamp
    await execute_write(
        "UPDATE academic_plans SET last_updated = ? WHERE id = ?",
        [datetime.now(timezone.utc).isoformat(), plan_id]
    )

    # Delete any draft for this requirement
    await execute_write(
        "DELETE FROM drafts WHERE plan_id = ? AND requirement_id = ?",
        [plan_id, req_id]
    )

    return await _get_requirement_with_courses(req_id)


@router.post("/{plan_id}/requirements/{req_id}/drafts")
async def save_draft(plan_id: str, req_id: str, body: dict):
    """Save/upsert draft for a requirement."""
    req = await execute_query(
        "SELECT * FROM requirements WHERE id = ? AND plan_id = ?",
        [req_id, plan_id], fetch_one=True
    )
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    changes_json = json.dumps(body.get("changes_json", {}))
    now = datetime.now(timezone.utc).isoformat()

    existing = await execute_query(
        "SELECT id FROM drafts WHERE plan_id = ? AND requirement_id = ?",
        [plan_id, req_id], fetch_one=True
    )

    if existing:
        await execute_write(
            "UPDATE drafts SET changes_json = ?, updated_at = ? WHERE id = ?",
            [changes_json, now, existing["id"]]
        )
    else:
        await execute_write(
            "INSERT INTO drafts (plan_id, requirement_id, changes_json, updated_at) VALUES (?, ?, ?, ?)",
            [plan_id, req_id, changes_json, now]
        )

    return {"status": "saved"}


@router.delete("/{plan_id}/requirements/{req_id}/drafts")
async def delete_draft(plan_id: str, req_id: str):
    """Delete draft for a requirement."""
    await execute_write(
        "DELETE FROM drafts WHERE plan_id = ? AND requirement_id = ?",
        [plan_id, req_id]
    )
    return {"status": "deleted"}


@router.get("/{plan_id}/drafts")
async def get_drafts(plan_id: str):
    """Get all drafts for a plan."""
    drafts_data = await execute_query(
        "SELECT * FROM drafts WHERE plan_id = ? ORDER BY updated_at DESC",
        [plan_id]
    )
    return [
        {
            "requirement_id": d["requirement_id"],
            "changes_json": json.loads(d["changes_json"]) if d["changes_json"] else {},
            "updated_at": d["updated_at"]
        }
        for d in drafts_data
    ]
