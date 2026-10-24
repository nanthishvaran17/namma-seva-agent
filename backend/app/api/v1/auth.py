import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.models.user import User, UserConsent
from backend.app.models.audit import AuditLogModel
from backend.app.models.task import UserTaskModel
from backend.app.models.document import UserDocumentModel
from backend.app.models.reminder import ReminderModel
from backend.app.models.conversation import ConversationModel
from backend.app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, ConsentCreate, ConsentResponse, UserProfileUpdate
from backend.app.api.deps import require_current_user
from backend.app.core.rate_limit import RateLimiter, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication & Privacy"])

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(key_prefix="auth_register"))]
)
async def register_citizen(user_in: UserCreate, request: Request, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    res = await db.execute(select(User).where(User.email == user_in.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A citizen account with this email already exists.")

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone_number=user_in.phone_number,
        preferred_language=user_in.preferred_language,
        role="CITIZEN"  # Role escalation prevention: public registration is always CITIZEN
    )
    db.add(new_user)
    await db.flush()

    client_ip = get_client_ip(request)

    # Initial DPDP consent
    initial_consent = UserConsent(
        user_id=new_user.id,
        consent_purpose="CITIZEN_SERVICE_ASSISTANCE",
        is_granted=True,
        ip_address=client_ip
    )
    db.add(initial_consent)

    # Audit log
    audit = AuditLogModel(
        user_id=new_user.id,
        action="USER_REGISTRATION",
        resource_type="USER",
        resource_id=new_user.id,
        ip_address=client_ip,
        details={"email": new_user.email}
    )
    db.add(audit)
    await db.commit()

    token = create_access_token({"sub": new_user.id, "role": new_user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(new_user)
    )

@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(RateLimiter(key_prefix="auth_login"))]
)
async def login_citizen(login_data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == login_data.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    client_ip = get_client_ip(request)
    audit = AuditLogModel(
        user_id=user.id,
        action="USER_LOGIN",
        resource_type="USER",
        resource_id=user.id,
        ip_address=client_ip,
        details={"email": user.email}
    )
    db.add(audit)
    await db.commit()

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(require_current_user)):
    return UserResponse.model_validate(current_user)

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    update_in: UserProfileUpdate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates allowed citizen profile attributes (full_name, phone_number, preferred_language).
    Role escalation prevention: role, email, and is_active cannot be modified here.
    """
    if update_in.full_name is not None:
        current_user.full_name = update_in.full_name
    if update_in.phone_number is not None:
        current_user.phone_number = update_in.phone_number
    if update_in.preferred_language is not None:
        current_user.preferred_language = update_in.preferred_language

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.post("/consents", response_model=ConsentResponse)
async def record_user_consent(
    consent_in: ConsentCreate,
    request: Request,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    consent = UserConsent(
        user_id=current_user.id,
        consent_purpose=consent_in.consent_purpose,
        is_granted=consent_in.is_granted,
        ip_address=request.client.host if request.client else None
    )
    db.add(consent)
    await db.commit()
    return ConsentResponse(
        id=consent.id,
        consent_purpose=consent.consent_purpose,
        is_granted=consent.is_granted,
        granted_at=consent.granted_at
    )

@router.get("/me/export")
async def export_citizen_data(
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Exports all personal citizen data in JSON format under the DPDP Act 2023."""
    tasks_res = await db.execute(select(UserTaskModel).where(UserTaskModel.user_id == current_user.id))
    tasks = tasks_res.scalars().all()

    docs_res = await db.execute(select(UserDocumentModel).where(UserDocumentModel.user_id == current_user.id))
    docs = docs_res.scalars().all()

    reminders_res = await db.execute(select(ReminderModel).where(ReminderModel.user_id == current_user.id))
    reminders = reminders_res.scalars().all()

    consents_res = await db.execute(select(UserConsent).where(UserConsent.user_id == current_user.id))
    consents = consents_res.scalars().all()

    export_payload = {
        "export_date": "2026-10-22",
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "preferred_language": current_user.preferred_language,
            "created_at": current_user.created_at.isoformat()
        },
        "tasks": [
            {
                "id": t.id,
                "service_id": t.service_id,
                "status": t.status,
                "form_data": t.form_data,
                "created_at": t.created_at.isoformat()
            }
            for t in tasks
        ],
        "documents": [
            {
                "id": d.id,
                "original_filename": d.original_filename,
                "doc_code": d.doc_code,
                "ocr_status": d.ocr_status,
                "extracted_fields": d.extracted_fields
            }
            for d in docs
        ],
        "reminders": [
            {
                "id": r.id,
                "title_en": r.title_en,
                "scheduled_for": r.scheduled_for.isoformat(),
                "status": r.status
            }
            for r in reminders
        ],
        "consents": [
            {
                "purpose": c.consent_purpose,
                "granted_at": c.granted_at.isoformat(),
                "is_granted": c.is_granted
            }
            for c in consents
        ]
    }
    return export_payload

@router.delete("/me/data", status_code=status.HTTP_200_OK)
async def delete_citizen_data(
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently erases all citizen data in compliance with the DPDP Act 2023:
    1. Physically deletes all encrypted document files and user upload directories from disk.
    2. Purges all user database records across documents, tasks, task events, reminders,
       conversations, messages, consents, audit logs, and user credentials.
    """
    import os
    import shutil
    user_id = current_user.id
    
    # 1. Physically delete all uploaded files and user directory from disk
    docs_res = await db.execute(select(UserDocumentModel).where(UserDocumentModel.user_id == user_id))
    user_docs = docs_res.scalars().all()
    for doc in user_docs:
        if doc.storage_path and os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except OSError:
                pass
                
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, user_id)
    if os.path.exists(user_upload_dir):
        shutil.rmtree(user_upload_dir, ignore_errors=True)

    # 2. Delete conversations and messages
    conv_res = await db.execute(select(ConversationModel.id).where(ConversationModel.user_id == user_id))
    conv_ids = [r[0] for r in conv_res.all()]
    if conv_ids:
        from backend.app.models.conversation import MessageModel
        await db.execute(delete(MessageModel).where(MessageModel.conversation_id.in_(conv_ids)))
        await db.execute(delete(ConversationModel).where(ConversationModel.id.in_(conv_ids)))

    # 3. Delete task events and tasks
    tasks_res = await db.execute(select(UserTaskModel.id).where(UserTaskModel.user_id == user_id))
    task_ids = [r[0] for r in tasks_res.all()]
    if task_ids:
        from backend.app.models.task import TaskEventModel
        await db.execute(delete(TaskEventModel).where(TaskEventModel.task_id.in_(task_ids)))
        await db.execute(delete(UserTaskModel).where(UserTaskModel.id.in_(task_ids)))

    # 4. Delete documents, reminders, consents, audit logs
    await db.execute(delete(UserDocumentModel).where(UserDocumentModel.user_id == user_id))
    await db.execute(delete(ReminderModel).where(ReminderModel.user_id == user_id))
    await db.execute(delete(UserConsent).where(UserConsent.user_id == user_id))
    await db.execute(delete(AuditLogModel).where(AuditLogModel.user_id == user_id))
    
    # 5. Delete user account
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()

    return {
        "status": "DELETED",
        "user_id": user_id,
        "files_purged": len(user_docs),
        "message": "All personal data, application tasks, and document metadata have been permanently erased from disk and database."
    }
