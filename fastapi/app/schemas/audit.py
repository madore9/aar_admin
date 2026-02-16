from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: str
    plan_id: str
    timestamp: str
    user: str
    action: str


class CreateAuditLogRequest(BaseModel):
    plan_id: str
    user: str
    action: str
