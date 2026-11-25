
import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.admin_dependencies import get_current_admin
from app.models import ApiKey, Client, AdminUser, AuditLog


router = APIRouter(
    prefix="/admin/clients",
    tags=["Admin API Key Management"],
)


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    expires_at: datetime | None = None


@router.post("/{client_id}/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(
    client_id: int,
    request: CreateApiKeyRequest,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Organization not found.",
        )

    if client.status != "active":
        raise HTTPException(
            status_code=400,
            detail="API keys can only be created for active organizations.",
        )

    if request.expires_at is not None:
        if request.expires_at.tzinfo is None:
            raise HTTPException(
                status_code=400,
                detail="Expiry date must include a timezone.",
            )

        if request.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=400,
                detail="Expiry date must be in the future.",
            )

    # Generate a cryptographically secure API key.
    random_part = secrets.token_urlsafe(32)
    plain_api_key = f"ocr_live_{random_part}"

    # Store only the SHA-256 hash, never the original key.
    key_hash = hashlib.sha256(
        plain_api_key.encode("utf-8")
    ).hexdigest()

    key_prefix = plain_api_key[:16]

    new_api_key = ApiKey(
        client_id=client.id,
        name=request.name.strip(),
        key_hash=key_hash,
        key_prefix=key_prefix,
        is_active=True,
        expires_at=request.expires_at,
    )


    try:
        db.add(new_api_key)
        db.flush()

        # Record API key creation in the audit log.
        audit_log = AuditLog(
            admin_user_id=current_admin.id,
            client_id=client.id,
            action="API_KEY_CREATED",
            description=(
                f"Created API key '{new_api_key.name}' "
                f"for organization '{client.organization_name}'"
            ),
            extra_data={
                "api_key_id": new_api_key.id,
                "key_name": new_api_key.name,
                "key_prefix": new_api_key.key_prefix,
            },
        )

        db.add(audit_log)
        db.commit()
        db.refresh(new_api_key)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create API key.",
        )


    # The plaintext key is returned only at creation time.
    return {
        "message": "API key created successfully.",
        "client_id": client.id,
        "organization_name": client.organization_name,
        "api_key_id": new_api_key.id,
        "key_name": new_api_key.name,
        "key_prefix": new_api_key.key_prefix,
        "api_key": plain_api_key,
        "expires_at": new_api_key.expires_at,
        "warning": "Copy and securely save this API key. It cannot be viewed again.",
    }
    
@router.get("/api-keys")
def list_api_keys(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    api_keys = (
        db.query(ApiKey, Client)
        .join(Client, ApiKey.client_id == Client.id)
        .order_by(ApiKey.id.desc())
        .all()
    )

    return [
        {
            "id": api_key.id,
            "client_id": api_key.client_id,
            "organization_name": client.organization_name,
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at,
            "last_used_at": api_key.last_used_at,
            "created_at": api_key.created_at,
            "revoked_at": api_key.revoked_at,
        }
        for api_key, client in api_keys
    ]
    
    
@router.post("/api-keys/{api_key_id}/revoke")
def revoke_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == api_key_id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="API key not found.",
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=400,
            detail="This API key has already been revoked.",
        )


    api_key.is_active = False
    api_key.revoked_at = datetime.now(timezone.utc)

    try:
        # Record API key revocation in the audit log.
        audit_log = AuditLog(
            admin_user_id=current_admin.id,
            client_id=api_key.client_id,
            action="API_KEY_REVOKED",
            description=(
                f"Revoked API key '{api_key.name}'"
            ),
            extra_data={
                "api_key_id": api_key.id,
                "key_name": api_key.name,
                "key_prefix": api_key.key_prefix,
            },
        )

        db.add(audit_log)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not revoke API key.",
        )

    return {
        "message": "API key revoked successfully.",
        "api_key_id": api_key.id,
        "status": "revoked",
    }


