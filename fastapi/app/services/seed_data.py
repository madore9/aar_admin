"""Seed data matching google_version/data/mockData.ts."""

from app.databases.sqlite_db import execute_query, execute_write

COURSES = [
    {"id": "CS50", "system_id": "100201", "title": "Introduction to Computer Science", "department": "Computer Science", "credits": 4},
    {"id": "CS50", "system_id": "100299", "title": "Introduction to Programming", "department": "Computer Science", "credits": 4},
    {"id": "CS51", "system_id": "100202", "title": "Abstraction and Design", "department": "Computer Science", "credits": 4},
    {"id": "CS51", "system_id": "100288", "title": "Abstraction and Design (Extension School)", "department": "Computer Science", "credits": 4},
    {"id": "CS61", "system_id": "100203", "title": "Systems Programming", "department": "Computer Science", "credits": 4},
    {"id": "CS121", "system_id": "100204", "title": "Theory of Computation", "department": "Computer Science", "credits": 4},
    {"id": "CS124", "system_id": "100205", "title": "Data Structures and Algorithms", "department": "Computer Science", "credits": 4},
    {"id": "CS181", "system_id": "100206", "title": "Machine Learning", "department": "Computer Science", "credits": 4},
    {"id": "CS182", "system_id": "100207", "title": "Deep Learning", "department": "Computer Science", "credits": 4},
    {"id": "MATH21a", "system_id": "200101", "title": "Multivariable Calculus", "department": "Mathematics", "credits": 4},
    {"id": "MATH21a", "system_id": "200199", "title": "Multivariable Calculus for Social Sciences", "department": "Mathematics", "credits": 4},
    {"id": "MATH21b", "system_id": "200102", "title": "Linear Algebra and Differential Equations", "department": "Mathematics", "credits": 4},
    {"id": "MATH21b", "system_id": "200188", "title": "Linear Algebra (Summer)", "department": "Mathematics", "credits": 4},
    {"id": "STAT110", "system_id": "300501", "title": "Introduction to Probability", "department": "Statistics", "credits": 4},
    {"id": "STAT110", "system_id": "300599", "title": "Probability Theory (Grad)", "department": "Statistics", "credits": 4},
    {"id": "STAT111", "system_id": "300502", "title": "Introduction to Statistical Inference", "department": "Statistics", "credits": 4},
    {"id": "PHY15a", "system_id": "400801", "title": "Introductory Mechanics and Relativity", "department": "Physics", "credits": 4},
    {"id": "PHY15a", "system_id": "400899", "title": "Honors Mechanics", "department": "Physics", "credits": 4},
    {"id": "ECON10a", "system_id": "500901", "title": "Principles of Economics: Microeconomics", "department": "Economics", "credits": 4},
    {"id": "ECON10a", "system_id": "500955", "title": "Microeconomics for Policy", "department": "Economics", "credits": 4},
    {"id": "ECON10b", "system_id": "500902", "title": "Principles of Economics: Macroeconomics", "department": "Economics", "credits": 4},
    {"id": "PSY1", "system_id": "600101", "title": "Introduction to Psychology", "department": "Psychology", "credits": 4},
    {"id": "PSY1", "system_id": "600102", "title": "General Psychology", "department": "Psychology", "credits": 4},
    {"id": "PSY1", "system_id": "600103", "title": "Mind, Brain, and Behavior", "department": "Psychology", "credits": 4},
    {"id": "ENG101", "system_id": "700101", "title": "The English Novel", "department": "English", "credits": 4},
    {"id": "ENG101", "system_id": "700102", "title": "Creative Writing: Fiction", "department": "English", "credits": 4},
]

PLANS = [
    {"id": "plan-cs-conc", "name": "Computer Science", "type": "Concentration", "last_updated": "2024-01-15"},
    {"id": "plan-cs-honors", "name": "Computer Science Honors Track", "type": "Concentration - Honors", "last_updated": "2024-01-10"},
    {"id": "plan-cs-secondary", "name": "Secondary Field in Computer Science", "type": "Secondary Field", "last_updated": "2024-02-01"},
    {"id": "plan-cs-joint", "name": "Joint Concentration in CS and Mathematics", "type": "Joint Concentration", "last_updated": "2024-01-20"},
]

REQUIREMENTS = [
    # plan-cs-conc
    {"id": "req-core", "plan_id": "plan-cs-conc", "title": "Core Programming", "description": "Foundational programming courses", "required_courses_count": 3, "required_units": 12, "sort_order": 0},
    {"id": "req-theory", "plan_id": "plan-cs-conc", "title": "Theory", "description": "Theoretical foundations of CS", "required_courses_count": 2, "required_units": 8, "sort_order": 1},
    {"id": "req-systems", "plan_id": "plan-cs-conc", "title": "Systems", "description": "Systems programming and design", "required_courses_count": 1, "required_units": 4, "sort_order": 2},
    {"id": "req-math", "plan_id": "plan-cs-conc", "title": "Mathematics", "description": "Required math courses", "required_courses_count": 2, "required_units": 8, "sort_order": 3},
    # plan-cs-honors
    {"id": "req-honors-core", "plan_id": "plan-cs-honors", "title": "Core Programming", "description": "Foundational programming courses", "required_courses_count": 3, "required_units": 12, "sort_order": 0},
    {"id": "req-honors-theory", "plan_id": "plan-cs-honors", "title": "Advanced Theory", "description": "Advanced theoretical courses", "required_courses_count": 3, "required_units": 12, "minimum_gpa": 3.5, "sort_order": 1},
    {"id": "req-honors-aiml", "plan_id": "plan-cs-honors", "title": "AI/ML Electives", "description": "Artificial intelligence and machine learning", "required_courses_count": 2, "required_units": 8, "minimum_gpa": 3.5, "sort_order": 2},
    {"id": "req-honors-math", "plan_id": "plan-cs-honors", "title": "Advanced Mathematics", "description": "Advanced math requirement", "required_courses_count": 2, "required_units": 8, "sort_order": 3},
    {"id": "req-honors-thesis", "plan_id": "plan-cs-honors", "title": "Thesis Requirement", "description": "Senior thesis", "required_courses_count": 1, "required_units": 4, "minimum_gpa": 3.5, "sort_order": 4},
    # plan-cs-secondary
    {"id": "req-secondary-intro", "plan_id": "plan-cs-secondary", "title": "Introductory Courses", "description": "Introductory CS courses", "required_courses_count": 2, "required_units": 8, "sort_order": 0},
    {"id": "req-secondary-elec", "plan_id": "plan-cs-secondary", "title": "CS Electives", "description": "Upper-level CS electives", "required_courses_count": 2, "required_units": 8, "sort_order": 1},
    # plan-cs-joint
    {"id": "req-joint-cs", "plan_id": "plan-cs-joint", "title": "Computer Science Core", "description": "Required CS courses", "required_courses_count": 4, "required_units": 16, "sort_order": 0},
    {"id": "req-joint-math", "plan_id": "plan-cs-joint", "title": "Mathematics Core", "description": "Required math courses", "required_courses_count": 3, "required_units": 12, "sort_order": 1},
    {"id": "req-joint-bridge", "plan_id": "plan-cs-joint", "title": "Bridge Courses", "description": "Interdisciplinary bridge courses", "required_courses_count": 2, "required_units": 8, "sort_order": 2},
]

REQUIREMENT_COURSES = [
    # req-core (plan-cs-conc)
    {"requirement_id": "req-core", "identifier": "100201", "is_wildcard": 0},
    {"requirement_id": "req-core", "identifier": "100202", "is_wildcard": 0},
    # req-theory
    {"requirement_id": "req-theory", "identifier": "100204", "is_wildcard": 0},
    {"requirement_id": "req-theory", "identifier": "100205", "is_wildcard": 0},
    # req-systems
    {"requirement_id": "req-systems", "identifier": "100203", "is_wildcard": 0},
    # req-math
    {"requirement_id": "req-math", "identifier": "200101", "is_wildcard": 0},
    {"requirement_id": "req-math", "identifier": "200102", "is_wildcard": 0},
    # req-honors-core
    {"requirement_id": "req-honors-core", "identifier": "100201", "is_wildcard": 0},
    {"requirement_id": "req-honors-core", "identifier": "100202", "is_wildcard": 0},
    {"requirement_id": "req-honors-core", "identifier": "100203", "is_wildcard": 0},
    # req-honors-theory
    {"requirement_id": "req-honors-theory", "identifier": "100204", "is_wildcard": 0},
    {"requirement_id": "req-honors-theory", "identifier": "100205", "is_wildcard": 0},
    # req-honors-aiml
    {"requirement_id": "req-honors-aiml", "identifier": "100206", "is_wildcard": 0},
    {"requirement_id": "req-honors-aiml", "identifier": "100207", "is_wildcard": 0},
    # req-honors-math
    {"requirement_id": "req-honors-math", "identifier": "300501", "is_wildcard": 0},
    # req-secondary-intro
    {"requirement_id": "req-secondary-intro", "identifier": "100201", "is_wildcard": 0},
    # req-secondary-elec (wildcard)
    {"requirement_id": "req-secondary-elec", "identifier": "CS1##", "is_wildcard": 1},
    # req-joint-cs
    {"requirement_id": "req-joint-cs", "identifier": "100201", "is_wildcard": 0},
    {"requirement_id": "req-joint-cs", "identifier": "100202", "is_wildcard": 0},
    {"requirement_id": "req-joint-cs", "identifier": "100204", "is_wildcard": 0},
    {"requirement_id": "req-joint-cs", "identifier": "100205", "is_wildcard": 0},
    # req-joint-math
    {"requirement_id": "req-joint-math", "identifier": "200101", "is_wildcard": 0},
    {"requirement_id": "req-joint-math", "identifier": "200102", "is_wildcard": 0},
]

COURSE_LISTS = [
    {"id": "list-cs-core", "name": "CS Core Courses", "description": "Foundational computer science courses"},
    {"id": "list-technical-electives", "name": "Technical Electives", "description": "Approved technical elective courses"},
    {"id": "list-humanities-breadth", "name": "Humanities Breadth Requirement", "description": "Approved humanities courses for breadth requirement"},
]

COURSE_LIST_COURSES = [
    {"course_list_id": "list-cs-core", "identifier": "100201", "is_wildcard": 0},
    {"course_list_id": "list-cs-core", "identifier": "100202", "is_wildcard": 0},
    {"course_list_id": "list-technical-electives", "identifier": "100206", "is_wildcard": 0},
    {"course_list_id": "list-technical-electives", "identifier": "100207", "is_wildcard": 0},
    {"course_list_id": "list-technical-electives", "identifier": "300502", "is_wildcard": 0},
    {"course_list_id": "list-humanities-breadth", "identifier": "500901", "is_wildcard": 0},
]


async def seed_database():
    """Insert seed data if tables are empty."""
    rows = await execute_query("SELECT COUNT(*) as cnt FROM courses")
    if rows[0]["cnt"] > 0:
        return

    from app.databases.sqlite_db import get_db
    db = await get_db()

    for c in COURSES:
        await db.execute(
            "INSERT INTO courses (system_id, id, title, department, credits) VALUES (?, ?, ?, ?, ?)",
            [c["system_id"], c["id"], c["title"], c["department"], c["credits"]],
        )

    for p in PLANS:
        await db.execute(
            "INSERT INTO academic_plans (id, name, type, last_updated) VALUES (?, ?, ?, ?)",
            [p["id"], p["name"], p["type"], p["last_updated"]],
        )

    for r in REQUIREMENTS:
        await db.execute(
            "INSERT INTO requirements (id, plan_id, title, description, required_courses_count, required_units, minimum_gpa, course_list_id, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [r["id"], r["plan_id"], r["title"], r["description"], r["required_courses_count"], r["required_units"], r.get("minimum_gpa"), r.get("course_list_id"), r["sort_order"]],
        )

    for rc in REQUIREMENT_COURSES:
        await db.execute(
            "INSERT INTO requirement_courses (requirement_id, identifier, is_wildcard) VALUES (?, ?, ?)",
            [rc["requirement_id"], rc["identifier"], rc["is_wildcard"]],
        )

    for cl in COURSE_LISTS:
        await db.execute(
            "INSERT INTO course_lists (id, name, description) VALUES (?, ?, ?)",
            [cl["id"], cl["name"], cl["description"]],
        )

    for clc in COURSE_LIST_COURSES:
        await db.execute(
            "INSERT INTO course_list_courses (course_list_id, identifier, is_wildcard) VALUES (?, ?, ?)",
            [clc["course_list_id"], clc["identifier"], clc["is_wildcard"]],
        )

    await db.commit()
