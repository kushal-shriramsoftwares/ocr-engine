
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.admin_dependencies import get_current_admin
from app.models import AdminUser, AuditLog, OCRService

router = APIRouter(
    prefix="/admin/services",
    tags=["Admin OCR Services"],
)


@router.get("/")
def get_ocr_services(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    services = (
        db.query(OCRService)
        .order_by(OCRService.id.asc())
        .all()
    )

    return [
        {
            "id": service.id,
            "service_code": service.service_code,
            "service_name": service.service_name,
            "description": service.description,
            "is_active": service.is_active,
            "created_at": service.created_at,
        }
        for service in services
    ]


@router.patch("/{service_id}/status")
def update_ocr_service_status(
    service_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    service = (
        db.query(OCRService)
        .filter(OCRService.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=404,
            detail="OCR service not found.",
        )


    service.is_active = is_active

    try:
        # Record OCR service status change.
        audit_log = AuditLog(
            admin_user_id=current_admin.id,
            client_id=None,
            action=(
                "OCR_SERVICE_ENABLED"
                if is_active
                else "OCR_SERVICE_DISABLED"
            ),
            description=(
                f"{'Enabled' if is_active else 'Disabled'} "
                f"OCR service: {service.service_name}"
            ),
            extra_data={
                "service_id": service.id,
                "service_code": service.service_code,
                "is_active": is_active,
            },
        )

        db.add(audit_log)
        db.commit()
        db.refresh(service)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update OCR service status.",
        )

    return {
        "message": "OCR service status updated successfully.",
        "id": service.id,
        "service_code": service.service_code,
        "is_active": service.is_active,
    }
