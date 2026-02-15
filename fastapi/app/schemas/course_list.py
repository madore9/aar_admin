from pydantic import BaseModel
from app.schemas.plan import RequirementCourse


class CourseList(BaseModel):
    id: str
    name: str
    description: str
    courses: list[RequirementCourse] = []
