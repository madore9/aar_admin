from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class PlanType(str, Enum):
    CONCENTRATION = "Concentration"
    HONORS = "Concentration - Honors"
    SECONDARY_FIELD = "Secondary Field"
    JOINT = "Joint Concentration"


class Scope(str, Enum):
    ALL = "all"
    INCOMING = "incoming"
    SELECTED_CLASSES = "selected_classes"


class RequirementCourse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    identifier: str
    is_wildcard: bool
    is_excluded: bool = False
    include_equivalent_courses: bool = False
    validity_type: Literal["ALWAYS", "TERMS", "DATE_RANGE"] = "ALWAYS"
    valid_terms: Optional[list[str]] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class Requirement(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    title: str
    description: str
    required_courses_count: int
    required_units: int
    minimum_gpa: Optional[float] = None
    courses: list[RequirementCourse] = []
    course_list_id: Optional[str] = None


class AcademicPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: str
    name: str
    type: PlanType
    last_updated: str
    requirements: list[Requirement] = []


class PendingChanges(BaseModel):
    additions: dict[str, RequirementCourse] = {}
    removals: list[str] = []
    modifications: dict[str, dict] = {}


class SaveChangesRequest(BaseModel):
    changes: PendingChanges
    scope: Scope = Scope.ALL


class AddRequirementRequest(BaseModel):
    title: str
    description: str
    required_courses_count: int = 0
    required_units: int = 0
    minimum_gpa: Optional[float] = None


class EditRequirementRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_courses_count: Optional[int] = None
    required_units: Optional[int] = None
    minimum_gpa: Optional[float] = None


class StatusResponse(BaseModel):
    status: str


class DraftResponse(BaseModel):
    requirement_id: str
    changes_json: dict = {}
    updated_at: str
