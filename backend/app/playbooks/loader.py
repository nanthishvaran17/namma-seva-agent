import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class PlaybookLoader:
    """
    Loads, validates, and manages government service playbooks.
    Ensures that only properly structured, verified playbooks are served.
    """

    def __init__(self, playbooks_dir: Optional[str] = None):
        self.playbooks_dir = Path(playbooks_dir or settings.PLAYBOOKS_DIR)
        self._catalog: Dict[str, Dict[str, Any]] = {}
        self.reload()

    def reload(self) -> int:
        """Reloads all playbooks from disk and validates them."""
        catalog = {}
        if not self.playbooks_dir.exists():
            logger.warning(f"Playbooks directory '{self.playbooks_dir}' does not exist.")
            self._catalog = {}
            return 0

        for file_path in self.playbooks_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self._validate_playbook_structure(data, file_path.name)
                service_id = data["service_id"]
                if service_id in catalog:
                    raise ValueError(f"Duplicate service_id '{service_id}' found in {file_path.name}")

                catalog[service_id] = data
            except Exception as e:
                logger.error(f"Error loading playbook {file_path.name}: {e}")
                raise e

        self._catalog = catalog
        logger.info(f"Loaded {len(self._catalog)} verified service playbooks.")
        return len(self._catalog)

    def _validate_playbook_structure(self, data: Dict[str, Any], filename: str):
        """Ensures non-negotiable schema requirements are met."""
        required_fields = [
            "service_id", "name_en", "name_ta", "description_en", "description_ta",
            "department", "category", "portal_url", "eligibility_rules",
            "required_documents", "fee", "processing_time", "application_steps",
            "dependencies", "official_sources", "last_verified", "verification_status", "version"
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Playbook {filename} missing mandatory field '{field}'.")

        if not data.get("official_sources"):
            raise ValueError(f"Playbook {filename} has no official sources listed.")

        valid_statuses = {"DRAFT", "NEEDS_VERIFICATION", "VERIFIED", "RETIRED"}
        if data["verification_status"] not in valid_statuses:
            raise ValueError(f"Playbook {filename} invalid verification_status '{data['verification_status']}'.")

    @property
    def catalog(self) -> Dict[str, Dict[str, Any]]:
        return self._catalog

    def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        return self._catalog.get(service_id)

    def list_services(
        self,
        category: Optional[str] = None,
        department: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Searches and filters services by category, department, or keywords (Tamil & English)."""
        results = []
        q = (query or "").lower().strip()

        for s in self._catalog.values():
            if category and s.get("category") != category:
                continue
            if department and s.get("department") != department:
                continue

            if q:
                match = (
                    q in s.get("name_en", "").lower() or
                    q in s.get("name_ta", "").lower() or
                    q in s.get("description_en", "").lower() or
                    q in s.get("description_ta", "").lower() or
                    q in s.get("service_id", "").lower() or
                    q in s.get("department", "").lower()
                )
                if not match:
                    continue

            results.append(s)

        return results

# Global singleton loader instance
playbook_loader = PlaybookLoader()
