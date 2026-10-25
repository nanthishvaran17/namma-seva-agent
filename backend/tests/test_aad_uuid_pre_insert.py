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
from sqlalchemy import select
from backend.app.db.session import AsyncSessionLocal
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


# ---------------------------------------------------------------------------
# Full lifecycle flush & reload tests across every construction path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestModelLifecycleRoundTrip:
    async def test_user_normal_init_flush_reload_round_trip(self):
        """Path 1: Standard User(**kwargs) init assigns UUID, flushes, and decrypts cleanly on reload."""
        email = f"user_init_{uuid.uuid4().hex[:6]}@example.com"
        test_phone = f"+9188{uuid.uuid4().int % 100000000:08d}"
        created_id = None

        async with AsyncSessionLocal() as session:
            user = User(
                email=email,
                hashed_password="hashed_pw_123",
                full_name="Anitha Muthukumar",
                phone_number=test_phone,
                role="CITIZEN",
                preferred_language="ta",
                is_active=True,
            )
            created_id = user.id
            assert created_id and len(created_id) == 36
            session.add(user)
            await session.commit()

        # Reload in a completely separate session
        async with AsyncSessionLocal() as session:
            reloaded = (await session.execute(select(User).where(User.id == created_id))).scalar_one()
            assert reloaded.id == created_id
            assert reloaded.full_name == "Anitha Muthukumar"
            assert reloaded.phone_number == test_phone
            assert reloaded.phone_blind_index is not None

    async def test_user_attribute_set_before_id_flush_reload_round_trip(self):
        """Path 2: Setting attributes when id is missing/None auto-assigns self.id, flushes and reloads cleanly."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        email = f"user_attr_first_{uuid.uuid4().hex[:6]}@example.com"
        test_phone = f"+9177{uuid.uuid4().int % 100000000:08d}"

        # Instantiate model and clear id to simulate attribute set before id is known/assigned
        user = User()
        user.id = None
        assert getattr(user, "id", None) is None

        # Call setters: first setter must auto-assign self.id
        user.full_name = "Karthik Subramanian"
        assigned_id = getattr(user, "id", None)
        assert assigned_id and len(assigned_id) == 36, "Setter must assign self.id first"

        # Second setter must reuse the exact same self.id
        user.phone_number = test_phone
        assert user.id == assigned_id, "Subsequent setter must reuse self.id"

        # Complete required DB fields
        user.email = email
        user.hashed_password = "hashed_pw_456"
        user.role = "CITIZEN"
        user.preferred_language = "ta"
        user.is_active = True
        user.created_at = now
        user.updated_at = now

        async with AsyncSessionLocal() as session:
            session.add(user)
            await session.commit()

        # Reload in a fresh session and verify clean round-trip decryption
        async with AsyncSessionLocal() as session:
            reloaded = (await session.execute(select(User).where(User.id == assigned_id))).scalar_one()
            assert reloaded.id == assigned_id
            assert reloaded.full_name == "Karthik Subramanian"
            assert reloaded.phone_number == test_phone

    async def test_user_orm_load_round_trip(self):
        """Path 3: Raw ORM load from DB populates _full_name column directly; property getter decrypts using row PK."""
        email = f"user_orm_{uuid.uuid4().hex[:6]}@example.com"
        user_id = str(uuid.uuid4())
        test_phone = f"+9166{uuid.uuid4().int % 100000000:08d}"

        async with AsyncSessionLocal() as session:
            user = User(
                id=user_id,
                email=email,
                hashed_password="hashed_pw_789",
                full_name="Meena Ramanathan",
                phone_number=test_phone,
            )
            session.add(user)
            await session.commit()

        # Open fresh session to force ORM hydration from SQL row
        async with AsyncSessionLocal() as session:
            loaded_user = await session.get(User, user_id)
            assert loaded_user is not None
            assert loaded_user.id == user_id
            assert loaded_user.full_name == "Meena Ramanathan"
            assert loaded_user.phone_number == test_phone

    async def test_document_normal_init_flush_reload_round_trip(self):
        """Path 1: Standard UserDocumentModel init flushes JSON fields and decrypts cleanly on reload."""
        u_id = str(uuid.uuid4())
        doc_id = None
        extracted_data = {"applicant_name": "Ravi", "annual_income": "72000"}
        corrections_data = {"annual_income": "80000"}

        async with AsyncSessionLocal() as session:
            # Need a user for FK
            u = User(id=u_id, email=f"doc_u_{uuid.uuid4().hex[:6]}@example.com", hashed_password="pw", full_name="Ravi")
            session.add(u)
            doc = UserDocumentModel(
                user_id=u_id,
                doc_code="income_cert",
                original_filename="income.pdf",
                storage_path="/var/docs/income.pdf",
                mime_type="application/pdf",
                file_size_bytes=45000,
                extracted_fields=extracted_data,
                user_corrections=corrections_data,
            )
            doc_id = doc.id
            session.add(doc)
            await session.commit()

        async with AsyncSessionLocal() as session:
            reloaded = (await session.execute(select(UserDocumentModel).where(UserDocumentModel.id == doc_id))).scalar_one()
            assert reloaded.id == doc_id
            assert reloaded.extracted_fields == extracted_data
            assert reloaded.user_corrections == corrections_data

    async def test_document_attribute_set_before_id_flush_reload_round_trip(self):
        """Path 2: Setting attributes when id is missing/None auto-assigns self.id, flushes and reloads cleanly."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        u_id = str(uuid.uuid4())
        extracted_data = {"ration_card_no": "0123456789"}
        corrections_data = {"family_members": 4}

        async with AsyncSessionLocal() as session:
            u = User(id=u_id, email=f"doc_u2_{uuid.uuid4().hex[:6]}@example.com", hashed_password="pw", full_name="User2")
            session.add(u)
            await session.commit()

        doc = UserDocumentModel()
        doc.id = None
        assert getattr(doc, "id", None) is None

        # Call extracted_fields setter before id is set
        doc.extracted_fields = extracted_data
        assigned_id = getattr(doc, "id", None)
        assert assigned_id and len(assigned_id) == 36

        # Call user_corrections setter: must reuse the assigned id
        doc.user_corrections = corrections_data
        assert doc.id == assigned_id

        # Set remaining DB fields
        doc.user_id = u_id
        doc.task_id = None
        doc.doc_code = "ration_card"
        doc.original_filename="ration.jpg"
        doc.storage_path="/var/docs/ration.jpg"
        doc.mime_type="image/jpeg"
        doc.file_size_bytes=24000
        doc.ocr_status = "PROCESSED"
        doc.is_verified_by_user = True
        doc.created_at = now
        doc.updated_at = now

        async with AsyncSessionLocal() as session:
            session.add(doc)
            await session.commit()

        # Reload in fresh session and verify clean round-trip
        async with AsyncSessionLocal() as session:
            reloaded = (await session.execute(select(UserDocumentModel).where(UserDocumentModel.id == assigned_id))).scalar_one()
            assert reloaded.id == assigned_id
            assert reloaded.extracted_fields == extracted_data
            assert reloaded.user_corrections == corrections_data

    async def test_document_orm_load_round_trip(self):
        """Path 3: Raw ORM load from DB decrypts JSON columns using row PK."""
        u_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        extracted_data = {"community": "BC", "caste": "Kongu Vellalar"}

        async with AsyncSessionLocal() as session:
            u = User(id=u_id, email=f"doc_u3_{uuid.uuid4().hex[:6]}@example.com", hashed_password="pw", full_name="User3")
            session.add(u)
            doc = UserDocumentModel(
                id=doc_id,
                user_id=u_id,
                doc_code="community_cert",
                original_filename="comm.pdf",
                storage_path="/var/docs/comm.pdf",
                mime_type="application/pdf",
                file_size_bytes=32000,
                extracted_fields=extracted_data,
            )
            session.add(doc)
            await session.commit()

        async with AsyncSessionLocal() as session:
            loaded_doc = await session.get(UserDocumentModel, doc_id)
            assert loaded_doc is not None
            assert loaded_doc.id == doc_id
            assert loaded_doc.extracted_fields == extracted_data

