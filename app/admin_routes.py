
from fastapi import APIRouter, Depends

from app.admin_dependencies import get_current_admin
from app.models import AdminUser

router = APIRouter(prefix="/admin", tags=["Admin Management"])


@router.get("/me")
def get_admin_profile(
    current_admin: AdminUser = Depends(get_current_admin),
):
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "email": current_admin.email,
        "is_active": current_admin.is_active,
    }
