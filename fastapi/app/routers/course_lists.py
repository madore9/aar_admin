import json
import uuid
from fastapi import APIRouter, HTTPException
from app.databases.sqlite_db import execute_query, execute_write
from app.schemas.course_list import CourseList, CourseListCreate, CourseListUpdate, CourseListCourseAdd
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


@router.post("/", status_code=201)
async def create_course_list(data: CourseListCreate):
    """Create a new course list."""
    list_id = f"list-{uuid.uuid4().hex[:8]}"

    await execute_write(
        "INSERT INTO course_lists (id, name, description) VALUES (?, ?, ?)",
        [list_id, data.name, data.description or ""]
    )

    return {"id": list_id, "name": data.name, "description": data.description or ""}


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


@router.put("/{list_id}")
async def update_course_list(list_id: str, data: CourseListUpdate):
    """Update a course list."""
    # Check exists
    existing = await execute_query(
        "SELECT id FROM course_lists WHERE id = ?",
        [list_id],
        fetch_one=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Course list not found")

    await execute_write(
        "UPDATE course_lists SET name = ?, description = ? WHERE id = ?",
        [data.name, data.description or "", list_id]
    )

    return {"id": list_id, "name": data.name, "description": data.description or ""}


@router.delete("/{list_id}", status_code=204)
async def delete_course_list(list_id: str):
    """Delete a course list."""
    # Check exists
    existing = await execute_query(
        "SELECT id FROM course_lists WHERE id = ?",
        [list_id],
        fetch_one=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Course list not found")

    # Delete courses first
    await execute_write("DELETE FROM course_list_courses WHERE course_list_id = ?", [list_id])
    # Delete list
    await execute_write("DELETE FROM course_lists WHERE id = ?", [list_id])

    return None


@router.post("/{list_id}/courses")
async def add_courses_to_list(list_id: str, data: CourseListCourseAdd):
    """Add courses to a course list."""
    # Check list exists
    existing = await execute_query(
        "SELECT id FROM course_lists WHERE id = ?",
        [list_id],
        fetch_one=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Course list not found")

    for course in data.courses:
        # Check if already exists
        existing_course = await execute_query(
            "SELECT identifier FROM course_list_courses WHERE course_list_id = ? AND identifier = ?",
            [list_id, course.identifier],
            fetch_one=True
        )
        if existing_course:
            continue  # Skip if already in list

        await execute_write(
            "INSERT INTO course_list_courses (course_list_id, identifier, is_wildcard) VALUES (?, ?, ?)",
            [list_id, course.identifier, 1 if course.is_wildcard else 0]
        )

    return {"message": "Courses added", "count": len(data.courses)}


@router.delete("/{list_id}/courses/{identifier}")
async def remove_course_from_list(list_id: str, identifier: str):
    """Remove a course from a course list."""
    await execute_write(
        "DELETE FROM course_list_courses WHERE course_list_id = ? AND identifier = ?",
        [list_id, identifier]
    )
    return None


@router.get("/{list_id}/usage")
async def get_course_list_usage(list_id: str):
    """Get all plans and requirements using this course list."""
    # First verify the list exists
    existing = await execute_query(
        "SELECT id FROM course_lists WHERE id = ?",
        [list_id],
        fetch_one=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Course list not found")

    # Find all requirements using this course list
    usage_data = await execute_query("""
        SELECT r.id as req_id, r.title as req_title, r.plan_id, p.name as plan_name, p.type as plan_type
        FROM requirements r
        JOIN academic_plans p ON r.plan_id = p.id
        WHERE r.course_list_id = ?
    """, [list_id])

    return {"usage": [
        {
            "plan_id": u["plan_id"],
            "plan_name": u["plan_name"],
            "plan_type": u["plan_type"],
            "req_id": u["req_id"],
            "req_title": u["req_title"]
        }
        for u in usage_data
    ]}
