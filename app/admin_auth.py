
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AdminUser
from app.security import verify_password, create_access_token


router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


class AdminLoginRequest(BaseModel):
    username_or_email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    credentials: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    identifier = credentials.username_or_email.strip().lower()

    admin = db.scalar(
        select(AdminUser).where(
            (AdminUser.username.ilike(identifier))
            | (AdminUser.email == identifier)
        )
    )

    if not admin or not verify_password(
        credentials.password,
        admin.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This administrator account is inactive.",
        )

    token = create_access_token(str(admin.id))

    return AdminLoginResponse(access_token=token)
