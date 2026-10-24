import logging
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.playbooks.loader import playbook_loader
from backend.app.models.playbook import ServicePlaybookModel

logger = logging.getLogger(__name__)

async def sync_playbooks_to_db(session: AsyncSession) -> int:
    """
    Synchronizes in-memory verified playbooks into the service_playbooks database table.
    Enforces referential integrity so foreign keys from user_tasks and service_sources resolve cleanly.
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
            # Sync any playbook updates
            existing.name_en = s_data["name_en"]
            existing.name_ta = s_data["name_ta"]
            existing.department = s_data["department"]
            existing.category = s_data["category"]
            existing.portal_url = s_data["portal_url"]
            existing.fee = s_data.get("fee", {})
            existing.processing_time = s_data.get("processing_time", {})
            existing.required_documents = s_data.get("required_documents", [])
            existing.dependencies = s_data.get("dependencies", [])
            existing.last_verified = s_data.get("last_verified")
            existing.verified_by = s_data.get("verified_by", "PENDING_OFFICIAL_VERIFICATION")
            existing.verification_status = s_data.get("verification_status", "NEEDS_VERIFICATION")

    if synced_count > 0:
        await session.commit()
        logger.info(f"Seeded {synced_count} playbooks into service_playbooks database table.")
    return synced_count
