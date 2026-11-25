
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.admin_dependencies import get_current_admin
from app.models import AccessRequest, AdminUser

router = APIRouter(
    prefix="/admin/access-requests",
    tags=["Admin Access Requests"],
)


@router.get("/pending")
def get_pending_requests(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    requests = db.scalars(
        select(AccessRequest)
        .where(AccessRequest.status == "pending")
        .order_by(AccessRequest.created_at.asc())
    ).all()

    return {
        "total": len(requests),
        "requests": [
            {
                "id": request.id,
                "organization_name": request.organization_name,
                "industry": request.industry,
                "contact_name": request.contact_name,
                "contact_email": request.contact_email,
                "contact_phone": request.contact_phone,
                "requested_services": request.requested_services,
                "status": request.status,
                "created_at": request.created_at,
            }
            for request in requests
        ],
    }
