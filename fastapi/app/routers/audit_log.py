import uuid
from datetime import datetime, timezone
from fastapi import APIRouter
from app.databases.sqlite_db import execute_query, execute_write
from app.schemas.audit import AuditLogEntry, CreateAuditLogRequest

router = APIRouter(prefix="/audit-log", tags=["audit_log"])


@router.get("/{plan_id}")
async def get_audit_log(plan_id: str):
    """Get audit entries for a plan, ordered by timestamp desc."""
    entries_data = await execute_query(
        "SELECT * FROM audit_log WHERE plan_id = ? ORDER BY timestamp DESC",
        [plan_id]
    )
    return [AuditLogEntry(**e) for e in entries_data]


@router.post("/", status_code=201)
async def create_audit_entry(request: CreateAuditLogRequest):
    """Create a new audit log entry."""
    entry_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    await execute_write(
        "INSERT INTO audit_log (id, plan_id, timestamp, user, action) VALUES (?, ?, ?, ?, ?)",
        [entry_id, request.plan_id, timestamp, request.user, request.action]
    )

    return AuditLogEntry(
        id=entry_id,
        plan_id=request.plan_id,
        timestamp=timestamp,
        user=request.user,
        action=request.action
    )
