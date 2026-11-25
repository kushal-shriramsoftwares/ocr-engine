
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.models import AdminUser
from app.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        admin_id = payload.get("sub")

        if not admin_id:
            raise ValueError("Missing token subject")

        admin_id = int(admin_id)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = db.scalar(
        select(AdminUser).where(AdminUser.id == admin_id)
    )

    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account not found or inactive.",
        )

    return admin
