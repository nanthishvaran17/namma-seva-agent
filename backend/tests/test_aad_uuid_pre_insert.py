"""
Verify that every model that uses AAD-bound FLE assigns a client-side UUID
BEFORE the encrypted setter is called, i.e., the row_id used in AAD is
the same UUID that would be stored as the primary key in the database.

This guarantees that decrypt_field(aad=compute_field_aad(table, col, pk))
will succeed after retrieval, and that no autoincrement ID is used as AAD.

Item 2 of final Wave-1 hardening commits.
"""
import uuid
import pytest
from backend.app.models.user import User
from backend.app.models.document import UserDocumentModel
from backend.app.core.crypto import compute_field_aad, decrypt_field


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class TestUserClientSideUUID:
    def test_uuid_assigned_before_full_name_encrypted(self):
        """
        User.__init__ must assign self.id BEFORE super().__init__ calls
        the full_name setter. The AAD must use that same id.
        """
        u = User(
            full_name="Test User",
            email="test@example.com",
            hashed_password="hashed",
        )
        # id must be a valid UUID string
        assert u.id and len(u.id) == 36, "id must be a 36-char UUID"
        parsed = uuid.UUID(u.id)  # raises if not a valid UUID
        assert str(parsed) == u.id

        # The encrypted column must be decryptable with AAD derived from that id
        aad = compute_field_aad("users", "full_name", u.id)
        decrypted = decrypt_field(u._full_name, associated_data=aad)
        assert decrypted == "Test User", (
            f"full_name AAD binding must use the assigned id; got '{decrypted}'"
        )

    def test_uuid_assigned_before_phone_number_encrypted(self):
        """Same guarantee for phone_number column."""
        u = User(
            full_name="Phone Test",
            email="phone@example.com",
            hashed_password="hashed",
            phone_number="9876543210",
        )
        assert u.id and len(u.id) == 36
        aad = compute_field_aad("users", "phone_number", u.id)
        decrypted = decrypt_field(u._phone_number, associated_data=aad)
        assert decrypted == "9876543210"

    def test_explicit_id_round_trips(self):
        """If caller supplies an id, that id is used for AAD binding."""
        fixed_id = str(uuid.uuid4())
        u = User(
            id=fixed_id,
            full_name="Named User",
            email="named@example.com",
            hashed_password="hashed",
        )
        assert u.id == fixed_id
        aad = compute_field_aad("users", "full_name", fixed_id)
        decrypted = decrypt_field(u._full_name, associated_data=aad)
        assert decrypted == "Named User"

    def test_no_autoincrement_id_in_user_model(self):
        """
        Confirm User.id is a string (UUID) primary key, not an integer
        autoincrement. If it were int, it would be unknown until DB flush.
        """
        from sqlalchemy import inspect as sa_inspect
        from backend.app.models.user import User as UserModel
        mapper = sa_inspect(UserModel)
        pk_col = mapper.mapper.primary_key[0]
        assert str(pk_col.type) in ("VARCHAR(36)", "TEXT", "String()"), (
            f"User primary key must be VARCHAR/UUID, got {pk_col.type}"
        )


# ---------------------------------------------------------------------------
# UserDocumentModel
# ---------------------------------------------------------------------------

class TestDocumentClientSideUUID:
    def test_uuid_assigned_before_extracted_fields_encrypted(self):
        """
        UserDocumentModel.__init__ must assign self.id before SQLAlchemy calls
        the extracted_fields setter, so the AAD row_id matches the stored PK.
        """
        doc = UserDocumentModel(
            user_id=str(uuid.uuid4()),
            doc_code="photo",
            original_filename="aadhaar.jpg",
            storage_path="/storage/aadhaar.jpg",
            mime_type="image/jpeg",
            file_size_bytes=102400,
            extracted_fields={"name": "Ravi Kumar"},
        )
        assert doc.id and len(doc.id) == 36
        uuid.UUID(doc.id)  # raises if not valid

        aad = compute_field_aad("user_documents", "extracted_fields", doc.id)
        decrypted = decrypt_field(doc._extracted_fields, associated_data=aad)
        import json
        assert json.loads(decrypted) == {"name": "Ravi Kumar"}

    def test_uuid_assigned_before_user_corrections_encrypted(self):
        """Same guarantee for user_corrections column."""
        doc = UserDocumentModel(
            user_id=str(uuid.uuid4()),
            doc_code="income_proof",
            original_filename="salary.pdf",
            storage_path="/storage/salary.pdf",
            mime_type="application/pdf",
            file_size_bytes=204800,
            user_corrections={"dob": "1990-01-01"},
        )
        assert doc.id and len(doc.id) == 36
        aad = compute_field_aad("user_documents", "user_corrections", doc.id)
        decrypted = decrypt_field(doc._user_corrections, associated_data=aad)
        import json
        assert json.loads(decrypted) == {"dob": "1990-01-01"}

    def test_no_autoincrement_id_in_document_model(self):
        """Confirm UserDocumentModel.id is a VARCHAR UUID, not an integer PK."""
        from sqlalchemy import inspect as sa_inspect
        from backend.app.models.document import UserDocumentModel as DocModel
        mapper = sa_inspect(DocModel)
        pk_col = mapper.mapper.primary_key[0]
        assert str(pk_col.type) in ("VARCHAR(36)", "TEXT", "String()"), (
            f"UserDocumentModel primary key must be VARCHAR/UUID, got {pk_col.type}"
        )
