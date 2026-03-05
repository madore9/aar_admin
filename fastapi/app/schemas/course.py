from pydantic import BaseModel, ConfigDict


class Course(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str           # Subject Catalog Number (e.g., CS50)
    system_id: str    # Unique 6-digit Course ID
    title: str
    department: str
    credits: int


class CourseSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    courses: list[Course]
    total: int


class CourseUsageEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    plan_name: str
    plan_id: str
    plan_type: str
    requirement_title: str
    requirement_id: str
    matched_by: str
    is_excluded: bool
