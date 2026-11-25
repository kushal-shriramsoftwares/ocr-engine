
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.models import AccessRequest

router = APIRouter(
    prefix="/access-requests",
    tags=["Organization Access Requests"],
)


class AccessRequestCreate(BaseModel):
    organization_name: str = Field(min_length=2, max_length=200)
    industry: str = Field(min_length=2, max_length=100)
    contact_name: str = Field(min_length=2, max_length=150)
    contact_email: str = Field(min_length=5, max_length=255)
    contact_phone: str = Field(min_length=5, max_length=30)
    requested_services: list[str] = Field(min_length=1)


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_access_request(
    request: AccessRequestCreate,
    db: Session = Depends(get_db),
):
    email = request.contact_email.strip().lower()

    existing_request = (
        db.query(AccessRequest)
        .filter(
            AccessRequest.contact_email == email,
            AccessRequest.status == "pending",
        )
        .first()
    )

    if existing_request:
        raise HTTPException(
            status_code=409,
            detail="A pending access request already exists for this email.",
        )

    new_request = AccessRequest(
        organization_name=request.organization_name.strip(),
        industry=request.industry.strip(),
        contact_name=request.contact_name.strip(),
        contact_email=email,
        contact_phone=request.contact_phone.strip(),
        requested_services=request.requested_services,
        status="pending",
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return {
        "message": "Access request submitted successfully.",
        "request_id": new_request.id,
        "status": new_request.status,
    }
