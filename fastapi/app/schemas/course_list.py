from pydantic import BaseModel
from app.schemas.plan import RequirementCourse


class CourseList(BaseModel):
    id: str
    name: str
    description: str
    courses: list[RequirementCourse] = []


class CourseListCreate(BaseModel):
    name: str
    description: str = ""


class CourseListUpdate(BaseModel):
    name: str
    description: str = ""


class CourseListCourseAdd(BaseModel):
    courses: list[RequirementCourse]
