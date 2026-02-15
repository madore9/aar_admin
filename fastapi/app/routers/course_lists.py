import json
from fastapi import APIRouter, HTTPException
from app.databases.sqlite_db import execute_query
from app.schemas.course_list import CourseList
from app.schemas.plan import RequirementCourse

router = APIRouter(prefix="/course-lists", tags=["course_lists"])


@router.get("/")
async def list_course_lists():
    """List all course lists (without courses)."""
    lists_data = await execute_query("SELECT * FROM course_lists ORDER BY name")
    return [
        {"id": cl["id"], "name": cl["name"], "description": cl.get("description", "")}
        for cl in lists_data
    ]


@router.get("/{list_id}")
async def get_course_list(list_id: str):
    """Get a single course list with its courses."""
    list_data = await execute_query(
        "SELECT * FROM course_lists WHERE id = ?",
        [list_id],
        fetch_one=True
    )
    if not list_data:
        raise HTTPException(status_code=404, detail="Course list not found")

    courses_data = await execute_query(
        "SELECT * FROM course_list_courses WHERE course_list_id = ?",
        [list_id]
    )

    courses = []
    for c in courses_data:
        valid_terms = json.loads(c["valid_terms"]) if c.get("valid_terms") else None
        courses.append(RequirementCourse(
            identifier=c["identifier"],
            is_wildcard=bool(c["is_wildcard"]),
            validity_type=c.get("validity_type", "ALWAYS"),
            valid_terms=valid_terms,
        ))

    return CourseList(
        id=list_data["id"],
        name=list_data["name"],
        description=list_data.get("description", ""),
        courses=courses
    )
