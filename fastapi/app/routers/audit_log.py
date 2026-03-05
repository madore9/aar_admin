import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Security

from app.databases.sqlite_db import execute_query, execute_write
from app.schemas.audit import AuditLogEntry, CreateAuditLogRequest
from app.utils.security import get_authenticated_user, KeyPermissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-log", tags=["audit_log"])


@router.get(
    "/{plan_id}",
    response_model=list[AuditLogEntry],
    description=f"Get audit log entries for a plan, newest first. Requires key permission: `{KeyPermissions.READ_AUDIT.value}`",
)
async def get_audit_log(
    plan_id: str,
    user=Security(get_authenticated_user, scopes=[KeyPermissions.READ_AUDIT]),
):
    """Get audit entries for a plan, ordered by timestamp desc."""
    logger.info(f"get_audit_log called, plan_id={plan_id}")
    entries_data = await execute_query(
        "SELECT * FROM audit_log WHERE plan_id = ? ORDER BY timestamp DESC",
        [plan_id]
    )
    return [AuditLogEntry(**e) for e in entries_data]


@router.post(
    "/",
    response_model=AuditLogEntry,
    status_code=201,
    description=f"Create a new audit log entry. Requires key permission: `{KeyPermissions.WRITE_AUDIT.value}`",
)
async def create_audit_entry(
    request: CreateAuditLogRequest,
    user=Security(get_authenticated_user, scopes=[KeyPermissions.WRITE_AUDIT]),
):
    """Create a new audit log entry."""
    logger.info(f"create_audit_entry called, plan_id={request.plan_id}, action={request.action}")
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
