
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.admin_auth import get_db
from app.admin_dependencies import get_current_admin
from app.models import (
    AccessRequest,
    AdminUser,
    AuditLog,
    Client,
    ClientPermission,
    OCRService,
    utc_now,
)

router = APIRouter(
    prefix="/admin/access-requests",
    tags=["Admin Approval"],
)


@router.post("/{request_id}/approve")
def approve_access_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # Find the access request.
    access_request = db.scalar(
        select(AccessRequest)
        .where(AccessRequest.id == request_id)
        .with_for_update()
    )

    if not access_request:
        raise HTTPException(
            status_code=404,
            detail="Access request not found.",
        )

    if access_request.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="This access request has already been reviewed.",
        )

    # Prevent duplicate client organizations.
    existing_client = db.scalar(
        select(Client).where(
            Client.contact_email == access_request.contact_email
        )
    )

    if existing_client:
        raise HTTPException(
            status_code=409,
            detail="A client with this contact email already exists.",
        )

    # Find all requested active OCR services.
    requested_codes = set(access_request.requested_services or [])

    services = db.scalars(
        select(OCRService).where(
            OCRService.service_code.in_(requested_codes),
            OCRService.is_active.is_(True),
        )
    ).all()

    available_codes = {service.service_code for service in services}

    if not requested_codes or available_codes != requested_codes:
        raise HTTPException(
            status_code=400,
            detail="One or more requested OCR services are invalid or inactive.",
        )

    try:
        # 1. Create the active client.
        client = Client(
            organization_name=access_request.organization_name,
            industry=access_request.industry,
            contact_name=access_request.contact_name,
            contact_email=access_request.contact_email,
            contact_phone=access_request.contact_phone,
            status="active",
        )

        db.add(client)
        db.flush()

        # 2. Assign requested OCR permissions.
        for service in services:
            permission = ClientPermission(
                client_id=client.id,
                service_id=service.id,
                is_enabled=True,
            )
            db.add(permission)

        # 3. Mark the access request as approved.
        access_request.status = "approved"
        access_request.reviewed_by = current_admin.id
        access_request.reviewed_at = utc_now()

        access_request.review_note = "Approved by super-admin."

        # Record the approval in the audit log.
        audit_log = AuditLog(
            admin_user_id=current_admin.id,
            client_id=client.id,
            action="ORGANIZATION_APPROVED",
            description=(
                f"Approved organization: {client.organization_name}"
            ),
            extra_data={
                "request_id": access_request.id,
                "organization_name": client.organization_name,
                "enabled_services": sorted(available_codes),
            },
        )

        db.add(audit_log)

        # Save everything as one transaction.
        db.commit()


        return {
            "message": "Organization approved successfully.",
            "request_id": access_request.id,
            "client_id": client.id,
            "organization_name": client.organization_name,
            "status": access_request.status,
            "enabled_services": sorted(available_codes),
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error. Approval was rolled back.",
        )

class RejectRequest(BaseModel):
    review_note: str = Field(
        min_length=3,
        max_length=500
    )


@router.post("/{request_id}/reject")
def reject_access_request(
    request_id: int,
    rejection: RejectRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    access_request = db.scalar(
        select(AccessRequest)
        .where(AccessRequest.id == request_id)
        .with_for_update()
    )

    if not access_request:
        raise HTTPException(
            status_code=404,
            detail="Access request not found.",
        )

    if access_request.status != "pending":
        raise HTTPException(
            status_code=409,
            detail="This access request has already been reviewed.",
        )

    try:
        access_request.status = "rejected"
        access_request.reviewed_by = current_admin.id
        access_request.reviewed_at = utc_now()

        access_request.review_note = rejection.review_note.strip()

        # Record the rejection in the audit log.
        audit_log = AuditLog(
            admin_user_id=current_admin.id,
            client_id=None,
            action="ORGANIZATION_REJECTED",
            description=(
                f"Rejected organization: {access_request.organization_name}"
            ),
            extra_data={
                "request_id": access_request.id,
                "organization_name": access_request.organization_name,
                "review_note": access_request.review_note,
            },
        )

        db.add(audit_log)

        db.commit()


        return {
            "message": "Organization access request rejected.",
            "request_id": access_request.id,
            "organization_name": access_request.organization_name,
            "status": access_request.status,
            "review_note": access_request.review_note,
        }

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error. Rejection was not saved.",
        )

