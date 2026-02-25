import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Security
from fastapi_cache.decorator import cache

from app.cache import aar_key_builder
from app.databases.sqlite_db import execute_query
from app.schemas.course import Course, CourseSearchResponse, CourseUsageEntry
from app.utils.security import get_authenticated_user, KeyPermissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get(
    "/",
    response_model=CourseSearchResponse,
    description=f"List or search courses. Requires key permission: `{KeyPermissions.READ_COURSES.value}`",
)
@cache(expire=600, namespace="courses", key_builder=aar_key_builder)
async def search_courses(
    q: str = Query(None, description="Search query"),
    field: str = Query("all", description="Search field: all, id, title, department"),
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
):
    """List/search courses with optional field filtering."""
    logger.info(f"search_courses called, q={q}, field={field}")

    # Validate field parameter
    valid_fields = ["all", "id", "title", "department", "system_id"]
    if field not in valid_fields:
        field = "all"
    
    if q:
        # Build query based on field
        if field == "all":
            where_clause = "WHERE id LIKE ? OR title LIKE ? OR department LIKE ? OR system_id LIKE ?"
            params = [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
        elif field == "id":
            where_clause = "WHERE id LIKE ?"
            params = [f"%{q}%"]
        elif field == "title":
            where_clause = "WHERE title LIKE ?"
            params = [f"%{q}%"]
        elif field == "department":
            where_clause = "WHERE department LIKE ?"
            params = [f"%{q}%"]
        elif field == "system_id":
            where_clause = "WHERE system_id LIKE ?"
            params = [f"%{q}%"]
        
        courses_data = await execute_query(
            f"SELECT * FROM courses {where_clause} ORDER BY id",
            params
        )
    else:
        courses_data = await execute_query("SELECT * FROM courses ORDER BY id")

    courses = [Course(**c) for c in courses_data]
    return CourseSearchResponse(courses=courses, total=len(courses))


@router.get(
    "/{system_id}",
    response_model=Course,
    description=f"Get a single course by system_id. Requires key permission: `{KeyPermissions.READ_COURSES.value}`",
)
@cache(expire=1800, namespace="courses", key_builder=aar_key_builder)
async def get_course(
    system_id: str,
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
):
    """Get a single course by system_id."""
    logger.info(f"get_course called, system_id={system_id}")
    course_data = await execute_query(
        "SELECT * FROM courses WHERE system_id = ?",
        [system_id],
        fetch_one=True
    )
    if not course_data:
        raise HTTPException(status_code=404, detail="Course not found")
    return Course(**course_data)


@router.get(
    "/{system_id}/usage",
    response_model=list[CourseUsageEntry],
    description=f"Get all plans/requirements using this course. Requires key permission: `{KeyPermissions.READ_COURSES.value}`",
)
async def get_course_usage(
    system_id: str,
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_COURSES]),
):
    """Get where this course is used across all plans."""
    logger.info(f"get_course_usage called, system_id={system_id}")
    course = await execute_query(
        "SELECT * FROM courses WHERE system_id = ?",
        [system_id],
        fetch_one=True
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course_catalog_id = course["id"]  # e.g. "CS121"

    # Find exact matches by system_id
    exact_matches = await execute_query(
        """SELECT rc.*, r.title as req_title, r.id as req_id, r.plan_id,
                  ap.name as plan_name, ap.type as plan_type
           FROM requirement_courses rc
           JOIN requirements r ON rc.requirement_id = r.id
           JOIN academic_plans ap ON r.plan_id = ap.id
           WHERE rc.identifier = ?""",
        [system_id]
    )

    # Find all wildcard entries
    wildcard_entries = await execute_query(
        """SELECT rc.*, r.title as req_title, r.id as req_id, r.plan_id,
                  ap.name as plan_name, ap.type as plan_type
           FROM requirement_courses rc
           JOIN requirements r ON rc.requirement_id = r.id
           JOIN academic_plans ap ON r.plan_id = ap.id
           WHERE rc.is_wildcard = 1"""
    )

    results = []
    seen = set()

    for match in exact_matches:
        key = (match["plan_id"], match["req_id"], match["identifier"])
        if key not in seen:
            seen.add(key)
            results.append({
                "plan_name": match["plan_name"],
                "plan_id": match["plan_id"],
                "plan_type": match["plan_type"],
                "requirement_title": match["req_title"],
                "requirement_id": match["req_id"],
                "matched_by": match["identifier"],
                "is_excluded": bool(match["is_excluded"])
            })

    for wc in wildcard_entries:
        pattern = wc["identifier"]
        # Convert wildcard: # = single char, * = any chars
        regex_pattern = "^" + pattern.replace("#", ".").replace("*", ".*") + "$"
        if re.match(regex_pattern, course_catalog_id):
            key = (wc["plan_id"], wc["req_id"], wc["identifier"])
            if key not in seen:
                seen.add(key)
                results.append({
                    "plan_name": wc["plan_name"],
                    "plan_id": wc["plan_id"],
                    "plan_type": wc["plan_type"],
                    "requirement_title": wc["req_title"],
                    "requirement_id": wc["req_id"],
                    "matched_by": wc["identifier"],
                    "is_excluded": bool(wc["is_excluded"])
                })

    return results
