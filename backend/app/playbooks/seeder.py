import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.playbooks.loader import playbook_loader
from backend.app.models.playbook import ServicePlaybookModel

logger = logging.getLogger(__name__)

async def sync_playbooks_to_db(session: AsyncSession) -> int:
    """
    Database is the ground truth for playbook verification and administration.
    1. Seeds initial playbooks into the service_playbooks table if not present.
    2. If a playbook exists in the DB, preserves the DB's verification status,
       reviewer, date, and review notes, syncing that state back into the in-memory
       catalog so restarts never overwrite DB verification state.
    """
    synced_count = 0
    for s_id, s_data in playbook_loader.catalog.items():
        existing = await session.get(ServicePlaybookModel, s_id)
        if not existing:
            model = ServicePlaybookModel(
                service_id=s_id,
                name_en=s_data["name_en"],
                name_ta=s_data["name_ta"],
                description_en=s_data["description_en"],
                description_ta=s_data["description_ta"],
                department=s_data["department"],
                category=s_data["category"],
                portal_url=s_data["portal_url"],
                application_url=s_data.get("application_url"),
                eligibility_rules=s_data.get("eligibility_rules", []),
                required_documents=s_data.get("required_documents", []),
                optional_documents=s_data.get("optional_documents", []),
                fee=s_data.get("fee", {}),
                processing_time=s_data.get("processing_time", {}),
                application_steps=s_data.get("application_steps", []),
                dependencies=s_data.get("dependencies", []),
                outputs=s_data.get("outputs", {}),
                last_verified=s_data.get("last_verified"),
                verified_by=s_data.get("verified_by", "PENDING_OFFICIAL_VERIFICATION"),
                verification_status=s_data.get("verification_status", "NEEDS_VERIFICATION"),
                version=s_data.get("version", "1.0.0"),
            )
            session.add(model)
            synced_count += 1
        else:
            # DB is source of truth for administrative and verification data.
            # Preserve DB status and sync it back to in-memory catalog
            s_data["verification_status"] = existing.verification_status
            s_data["verified_by"] = existing.verified_by
            s_data["last_verified"] = existing.last_verified
            s_data["review_notes"] = existing.review_notes

    if synced_count > 0:
        await session.commit()
        logger.info(f"Seeded {synced_count} playbooks into service_playbooks database table.")

    # Reconcile all DB models into in-memory catalog
    all_res = await session.execute(select(ServicePlaybookModel))
    for db_row in all_res.scalars().all():
        if db_row.service_id in playbook_loader.catalog:
            cat = playbook_loader.catalog[db_row.service_id]
            cat["verification_status"] = db_row.verification_status
            cat["verified_by"] = db_row.verified_by
            cat["last_verified"] = db_row.last_verified
            cat["review_notes"] = db_row.review_notes

    return synced_count


async def detect_playbook_divergence(session: AsyncSession) -> List[Dict[str, Any]]:
    """
    Compares DB ground truth with disk JSON files to detect and alert on any silent divergence.
    """
    divergences = []
    playbooks_dir = Path(settings.PLAYBOOKS_DIR)

    all_res = await session.execute(select(ServicePlaybookModel))
    db_playbooks = {row.service_id: row for row in all_res.scalars().all()}

    for s_id, db_row in db_playbooks.items():
        disk_file = playbooks_dir / f"{s_id}.json"
        if not disk_file.exists():
            divergences.append({
                "service_id": s_id,
                "issue": "FILE_MISSING_ON_DISK",
                "details": f"Playbook exists in DB but not on disk at {disk_file.name}"
            })
            continue

        try:
            with open(disk_file, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
        except Exception as e:
            divergences.append({
                "service_id": s_id,
                "issue": "DISK_FILE_CORRUPT",
                "details": str(e)
            })
            continue

        field_diffs = {}
        if db_row.verification_status != disk_data.get("verification_status"):
            field_diffs["verification_status"] = {
                "db": db_row.verification_status,
                "disk": disk_data.get("verification_status")
            }
        if db_row.last_verified != disk_data.get("last_verified"):
            field_diffs["last_verified"] = {
                "db": db_row.last_verified,
                "disk": disk_data.get("last_verified")
            }
        if db_row.verified_by != disk_data.get("verified_by"):
            field_diffs["verified_by"] = {
                "db": db_row.verified_by,
                "disk": disk_data.get("verified_by")
            }

        if field_diffs:
            divergences.append({
                "service_id": s_id,
                "issue": "FIELD_DIVERGENCE",
                "differences": field_diffs
            })

    return divergences


async def export_db_playbooks_to_disk(session: AsyncSession) -> int:
    """
    Explicitly exports all playbooks from the database source of truth to disk JSON files.
    Only executed via explicit operator command or API endpoint.
    """
    playbooks_dir = Path(settings.PLAYBOOKS_DIR)
    playbooks_dir.mkdir(parents=True, exist_ok=True)

    all_res = await session.execute(select(ServicePlaybookModel))
    db_playbooks = all_res.scalars().all()
    exported_count = 0

    for row in db_playbooks:
        file_path = playbooks_dir / f"{row.service_id}.json"
        data = {
            "service_id": row.service_id,
            "name_en": row.name_en,
            "name_ta": row.name_ta,
            "description_en": row.description_en,
            "description_ta": row.description_ta,
            "department": row.department,
            "category": row.category,
            "portal_url": row.portal_url,
            "application_url": row.application_url,
            "eligibility_rules": row.eligibility_rules,
            "required_documents": row.required_documents,
            "optional_documents": row.optional_documents,
            "fee": row.fee,
            "processing_time": row.processing_time,
            "application_steps": row.application_steps,
            "dependencies": row.dependencies,
            "outputs": row.outputs,
            "last_verified": row.last_verified,
            "verified_by": row.verified_by,
            "verification_status": row.verification_status,
            "version": row.version,
            "review_notes": row.review_notes,
            "official_sources": [
                {"title": "Tamil Nadu e-Sevai Portal", "url": row.portal_url}
            ]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        exported_count += 1

    playbook_loader.reload()
    return exported_count
