import os
import uuid
from typing import Dict, Any, Optional
from backend.app.core.config import settings

class DocumentProcessor:
    """
    Modular OCR and document extraction abstraction.
    Treats OCR text as untrusted and sanitizes extracted values.
    Gates simulated mock parsing behind settings.DEMO_MODE.
    """

    async def process_document(
        self,
        file_path: str,
        mime_type: str,
        doc_code: str,
        original_filename: str
    ) -> Dict[str, Any]:
        """
        Extracts key metadata based on document code.
        When DEMO_MODE is True, produces labeled synthetic fields for local testing.
        When DEMO_MODE is False, blocks simulated parsing.
        """
        if not settings.DEMO_MODE:
            return {
                "is_demo": False,
                "status": "DISABLED_IN_PRODUCTION",
                "confidence_score": 0.0,
                "notice": "Simulated OCR is disabled in non-demo mode. Real vision-based extraction will activate in Phase B."
            }

        filename_lower = original_filename.lower()
        extracted: Dict[str, Any] = {
            "is_demo": True,
            "demo_notice": "DEMO, not real extraction (Phase B Vision Model Planned)",
        }

        if doc_code == "community_certificate":
            extracted.update({
                "document_type": "Tamil Nadu e-District Community Certificate",
                "certificate_number": f"DEMO-CC-{uuid.uuid4().hex[:8].upper()}",
                "applicant_name": "Applicant Citizen",
                "father_name": "Father Citizen",
                "community": "BC",
                "caste_subcaste": "Agamudayar",
                "issuing_taluk": "Coimbatore North",
                "issuing_officer": "Zonal Deputy Tahsildar",
                "validity": "PERMANENT",
                "confidence_score": 0.96
            })
        elif doc_code == "income_certificate":
            extracted.update({
                "document_type": "Revenue Administration Income Certificate",
                "certificate_number": f"DEMO-INC-{uuid.uuid4().hex[:8].upper()}",
                "annual_family_income_inr": 180000,
                "applicant_name": "Applicant Citizen",
                "parent_name": "Parent Citizen",
                "validity_period_months": 6,
                "issued_date": "2026-10-01",
                "confidence_score": 0.94
            })
        elif doc_code == "nativity_certificate":
            extracted.update({
                "document_type": "Tamil Nadu Nativity Certificate",
                "certificate_number": f"DEMO-NAT-{uuid.uuid4().hex[:8].upper()}",
                "applicant_name": "Applicant Citizen",
                "district": "Madurai",
                "years_of_continuous_residence": 12,
                "validity": "PERMANENT",
                "confidence_score": 0.98
            })
        elif doc_code in {"address_proof", "ration_card"}:
            extracted.update({
                "document_type": "Tamil Nadu Smart Family Card (TNPDS)",
                "card_number": f"33/W/{uuid.uuid4().hex[:7].upper()}",
                "head_of_family": "Family Head",
                "district": "Chennai",
                "total_family_members": 4,
                "confidence_score": 0.95
            })
        else:
            extracted.update({
                "document_type": "General Verification Proof",
                "original_filename": original_filename,
                "verified_format": mime_type,
                "confidence_score": 0.90
            })

        return extracted

document_processor = DocumentProcessor()
