from pydantic import BaseModel, ConfigDict
from app.schemas.plan import RequirementCourse


class CourseList(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

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


class CourseListSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    name: str
    description: str = ""


class CourseListUsageEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    plan_id: str
    plan_name: str
    plan_type: str
    req_id: str
    req_title: str


class CourseListUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    usage: list[CourseListUsageEntry]


class CourseListCoursesAddedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    message: str
    count: int
