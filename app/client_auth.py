
import hashlib
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.models import ApiKey, Client


api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def get_current_client(
    request: Request,
    api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> Client:

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required.",
        )

    key_hash = hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()

    stored_key = db.scalar(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    )

    if not stored_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    if not stored_key.is_active or stored_key.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is inactive or revoked.",
        )

    now = datetime.now(timezone.utc)

    if stored_key.expires_at is not None:
        expiry = stored_key.expires_at

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if expiry <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has expired.",
            )

    client = db.scalar(
        select(Client).where(Client.id == stored_key.client_id)
    )

    if not client or client.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive or suspended.",
        )

    stored_key.last_used_at = now
    db.commit()
    
    request.state.api_key_id = stored_key.id


    return client
