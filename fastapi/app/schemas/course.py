from pydantic import BaseModel


class Course(BaseModel):
    id: str           # Subject Catalog Number (e.g., CS50)
    system_id: str    # Unique 6-digit Course ID
    title: str
    department: str
    credits: int


class CourseSearchResponse(BaseModel):
    courses: list[Course]
    total: int
