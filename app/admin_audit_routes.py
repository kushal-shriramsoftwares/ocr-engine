
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.admin_dependencies import get_current_admin
from app.models import AdminUser, AuditLog

router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["Admin Audit Logs"],
)


@router.get("/")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(500)
        .all()
    )

    return [
        {
            "id": log.id,
            "admin_user_id": log.admin_user_id,
            "client_id": log.client_id,
            "action": log.action,
            "description": log.description,
            "extra_data": log.extra_data,
            "created_at": log.created_at,
        }
        for log in logs
    ]
