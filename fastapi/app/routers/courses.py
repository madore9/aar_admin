import re
from fastapi import APIRouter, HTTPException, Query
from app.databases.sqlite_db import execute_query
from app.schemas.course import Course, CourseSearchResponse

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/")
async def search_courses(q: str = Query(None, description="Search query")):
    """List/search courses."""
    if q:
        courses_data = await execute_query(
            """SELECT * FROM courses
               WHERE id LIKE ? OR title LIKE ? OR department LIKE ? OR system_id LIKE ?
               ORDER BY id""",
            [f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"]
        )
    else:
        courses_data = await execute_query("SELECT * FROM courses ORDER BY id")

    courses = [Course(**c) for c in courses_data]
    return CourseSearchResponse(courses=courses, total=len(courses))


@router.get("/{system_id}")
async def get_course(system_id: str):
    """Get a single course by system_id."""
    course_data = await execute_query(
        "SELECT * FROM courses WHERE system_id = ?",
        [system_id],
        fetch_one=True
    )
    if not course_data:
        raise HTTPException(status_code=404, detail="Course not found")
    return Course(**course_data)


@router.get("/{system_id}/usage")
async def get_course_usage(system_id: str):
    """Get where this course is used across all plans."""
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
