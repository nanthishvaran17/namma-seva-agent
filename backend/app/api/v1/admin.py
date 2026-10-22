from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.audit import AuditLogModel
from backend.app.models.task import UserTaskModel
from backend.app.models.document import UserDocumentModel
from backend.app.api.deps import require_admin_user
from backend.app.playbooks.loader import playbook_loader

router = APIRouter(prefix="/admin", tags=["Admin & Knowledge Management"])

class StatusUpdateRequest(BaseModel):
    verification_status: str
    review_notes: Optional[str] = None

@router.get("/playbooks")
async def get_all_playbooks(admin_user: User = Depends(require_admin_user)):
    return list(playbook_loader.catalog.values())

@router.patch("/playbooks/{service_id}/status")
async def update_playbook_verification_status(
    service_id: str,
    update: StatusUpdateRequest,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db)
):
    service = playbook_loader.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")

    valid_statuses = {"DRAFT", "NEEDS_VERIFICATION", "VERIFIED", "RETIRED"}
    if update.verification_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    prev = service.get("verification_status")
    service["verification_status"] = update.verification_status
    if update.review_notes:
        service["review_notes"] = update.review_notes

    audit = AuditLogModel(
        user_id=admin_user.id,
        action="PLAYBOOK_VERIFICATION_STATUS_CHANGE",
        resource_type="PLAYBOOK",
        resource_id=service_id,
        details={
            "previous_status": prev,
            "new_status": update.verification_status,
            "reviewer": admin_user.email
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "service_id": service_id,
        "verification_status": update.verification_status,
        "message": f"Service status successfully updated to {update.verification_status}"
    }

@router.get("/metrics")
async def get_system_metrics(
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Aggregate operational metrics without exposing citizen PII."""
    users_count = await db.scalar(select(func.count(User.id)))
    tasks_count = await db.scalar(select(func.count(UserTaskModel.id)))
    docs_count = await db.scalar(select(func.count(UserDocumentModel.id)))

    # Status breakdown
    status_counts_res = await db.execute(
        select(UserTaskModel.status, func.count(UserTaskModel.id))
        .group_by(UserTaskModel.status)
    )
    tasks_by_status = {row[0]: row[1] for row in status_counts_res.all()}

    return {
        "total_citizens_registered": users_count or 0,
        "total_application_tasks": tasks_count or 0,
        "total_documents_analyzed": docs_count or 0,
        "tasks_by_status": tasks_by_status,
        "total_playbooks_in_catalog": len(playbook_loader.catalog)
    }

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 50,
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AuditLogModel)
        .order_by(AuditLogModel.created_at.desc())
        .limit(limit)
    )
    logs = res.scalars().all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "timestamp": l.created_at.isoformat(),
            "details": l.details
        }
        for l in logs
    ]
