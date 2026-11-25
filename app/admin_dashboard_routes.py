
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.admin_auth import get_db
from app.admin_dependencies import get_current_admin
from app.models import (
    AdminUser,
    Client,
    ApiKey,
    AccessRequest,
    UsageLog,
)

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
)


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    now = datetime.now(timezone.utc)

    total_organizations = (
        db.query(func.count(Client.id)).scalar() or 0
    )

    active_api_keys = (
        db.query(func.count(ApiKey.id))
        .filter(
            ApiKey.is_active.is_(True),
            ApiKey.revoked_at.is_(None),
            or_(
                ApiKey.expires_at.is_(None),
                ApiKey.expires_at > now,
            ),
        )
        .scalar()
        or 0
    )

    pending_access_requests = (
        db.query(func.count(AccessRequest.id))
        .filter(AccessRequest.status == "pending")
        .scalar()
        or 0
    )

    total_ocr_requests = (
        db.query(func.count(UsageLog.id)).scalar() or 0
    )

    return {
        "total_organizations": total_organizations,
        "active_api_keys": active_api_keys,
        "pending_access_requests": pending_access_requests,
        "total_ocr_requests": total_ocr_requests,
    }
@router.get("/organizations")
def get_organizations(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    organizations = db.query(Client).order_by(Client.id.desc()).all()

    return [
        {
            "id": org.id,
            "organization_name": org.organization_name,
            "industry": org.industry,
            "contact_name": org.contact_name,
            "contact_email": org.contact_email,
            "contact_phone": org.contact_phone,
            "status": org.status,
            "created_at": org.created_at,
        }
        for org in organizations
    ]

@router.get("/usage-analytics")
def get_usage_analytics(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    # 1. Total requests
    total_requests = (
        db.query(func.count(UsageLog.id)).scalar() or 0
    )

    # 2. Successful requests
    successful_requests = (
        db.query(func.count(UsageLog.id))
        .filter(
            UsageLog.http_status >= 200,
            UsageLog.http_status < 300,
        )
        .scalar()
        or 0
    )

    # 3. Failed requests
    failed_requests = (
        db.query(func.count(UsageLog.id))
        .filter(UsageLog.http_status >= 400)
        .scalar()
        or 0
    )

    # 4. Average processing time
    average_duration = (
        db.query(func.avg(UsageLog.duration_ms)).scalar()
    )

    # 5. Requests grouped by organization
    organization_usage = (
        db.query(
            Client.id,
            Client.organization_name,
            func.count(UsageLog.id).label("total_requests"),
        )
        .join(UsageLog, UsageLog.client_id == Client.id)
        .group_by(Client.id, Client.organization_name)
        .order_by(func.count(UsageLog.id).desc())
        .all()
    )

    # 6. Requests grouped by OCR service
    service_usage = (
        db.query(
            UsageLog.service_code,
            func.count(UsageLog.id).label("total_requests"),
        )
        .group_by(UsageLog.service_code)
        .order_by(func.count(UsageLog.id).desc())
        .all()
    )

    # 7. Daily request counts
    daily_usage = (
        db.query(
            func.date(UsageLog.created_at).label("date"),
            func.count(UsageLog.id).label("total_requests"),
        )
        .group_by(func.date(UsageLog.created_at))
        .order_by(func.date(UsageLog.created_at).asc())
        .all()
    )

    return {
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "average_duration_ms": round(
            float(average_duration or 0), 2
        ),
        "organization_usage": [
            {
                "organization_id": row.id,
                "organization_name": row.organization_name,
                "total_requests": row.total_requests,
            }
            for row in organization_usage
        ],
        "service_usage": [
            {
                "service_code": row.service_code,
                "total_requests": row.total_requests,
            }
            for row in service_usage
        ],
        "daily_usage": [
            {
                "date": str(row.date),
                "total_requests": row.total_requests,
            }
            for row in daily_usage
        ],
    }
