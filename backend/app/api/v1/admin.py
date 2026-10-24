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
from backend.app.core.config import settings
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
    from datetime import datetime, timezone
    from pathlib import Path
    import json
    from backend.app.models.playbook import ServicePlaybookModel

    service = playbook_loader.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found.")

    valid_statuses = {"DRAFT", "NEEDS_VERIFICATION", "VERIFIED", "RETIRED"}
    new_status = update.verification_status.strip().upper()
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    prev_status = service.get("verification_status")
    prev_verified_by = service.get("verified_by")
    prev_last_verified = service.get("last_verified")

    # Invariant enforcement: only verified status can have last_verified date
    if new_status == "VERIFIED":
        new_verified_by = admin_user.email
        new_last_verified = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    else:
        new_verified_by = "PENDING_OFFICIAL_VERIFICATION"
        new_last_verified = None

    # 1. Update in-memory loader catalog
    service["verification_status"] = new_status
    service["verified_by"] = new_verified_by
    service["last_verified"] = new_last_verified
    if update.review_notes is not None:
        service["review_notes"] = update.review_notes

    # 2. Persist to database
    db_model = await db.get(ServicePlaybookModel, service_id)
    if db_model:
        db_model.verification_status = new_status
        db_model.verified_by = new_verified_by
        db_model.last_verified = new_last_verified
        if update.review_notes is not None:
            db_model.review_notes = update.review_notes
    else:
        db_model = ServicePlaybookModel(
            service_id=service_id,
            name_en=service.get("name_en", service_id),
            name_ta=service.get("name_ta", service_id),
            description_en=service.get("description_en", ""),
            description_ta=service.get("description_ta", ""),
            department=service.get("department", "TNeGA"),
            category=service.get("category", "General"),
            portal_url=service.get("portal_url", ""),
            application_url=service.get("application_url"),
            eligibility_rules=service.get("eligibility_rules", []),
            required_documents=service.get("required_documents", []),
            optional_documents=service.get("optional_documents", []),
            fee=service.get("fee", {}),
            processing_time=service.get("processing_time", {}),
            application_steps=service.get("application_steps", []),
            dependencies=service.get("dependencies", []),
            outputs=service.get("outputs", {}),
            verification_status=new_status,
            verified_by=new_verified_by,
            last_verified=new_last_verified,
            version=service.get("version", "1.0.0"),
            review_notes=update.review_notes
        )
        db.add(db_model)

    # 3. Persist to JSON file on disk
    playbook_file = Path(settings.PLAYBOOKS_DIR) / f"{service_id}.json"
    if playbook_file.exists():
        try:
            with open(playbook_file, "w", encoding="utf-8") as f:
                json.dump(service, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to persist playbook to disk: {e}")

    # 4. Audit Log with who, when, old_status, new_status
    now_iso = datetime.now(timezone.utc).isoformat()
    audit = AuditLogModel(
        user_id=admin_user.id,
        action="PLAYBOOK_VERIFICATION_STATUS_CHANGE",
        resource_type="PLAYBOOK",
        resource_id=service_id,
        details={
            "who": admin_user.email,
            "when": now_iso,
            "old_status": prev_status,
            "new_status": new_status,
            "old_verified_by": prev_verified_by,
            "new_verified_by": new_verified_by,
            "old_last_verified": prev_last_verified,
            "new_last_verified": new_last_verified,
            "review_notes": update.review_notes
        }
    )
    db.add(audit)
    await db.commit()

    return {
        "service_id": service_id,
        "verification_status": new_status,
        "verified_by": new_verified_by,
        "last_verified": new_last_verified,
        "message": f"Service status successfully updated to {new_status} by {admin_user.email}"
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
