import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.models.document import UserDocumentModel
from backend.app.models.task import UserTaskModel
from backend.app.models.user import User
from backend.app.schemas.document import DocumentResponse, DocumentCorrectionRequest
from backend.app.api.deps import require_current_user
from backend.app.documents.processor import document_processor

router = APIRouter(prefix="/documents", tags=["Document Intelligence & Processing"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_code: str = Form(...),
    task_id: Optional[str] = Form(None),
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate MIME type
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{file.content_type}'. Allowed: PDF, JPEG, PNG, WebP."
        )

    # Read and validate size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
        )

    # Save to disk in isolated directory with random UUID
    file_ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
    safe_name = f"{uuid.uuid4().hex}{file_ext}"
    user_storage_dir = os.path.join(settings.UPLOAD_DIR, current_user.id)
    os.makedirs(user_storage_dir, exist_ok=True)
    stored_path = os.path.join(user_storage_dir, safe_name)

    with open(stored_path, "wb") as f:
        f.write(content)

    # OCR extraction
    extracted = await document_processor.process_document(
        file_path=stored_path,
        mime_type=file.content_type,
        doc_code=doc_code,
        original_filename=file.filename or "upload"
    )

    doc_model = UserDocumentModel(
        user_id=current_user.id,
        task_id=task_id,
        doc_code=doc_code,
        original_filename=file.filename or "uploaded_document",
        storage_path=stored_path,
        mime_type=file.content_type,
        file_size_bytes=len(content),
        ocr_status="DEMO_PROCESSED" if settings.DEMO_MODE else "PENDING_PHASE_B_OCR",
        extracted_fields=extracted,
        is_verified_by_user=False
    )
    db.add(doc_model)
    await db.commit()

    return DocumentResponse.model_validate(doc_model)

@router.get("", response_model=List[DocumentResponse])
async def list_user_documents(
    task_id: Optional[str] = None,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(UserDocumentModel).where(UserDocumentModel.user_id == current_user.id)
    if task_id:
        query = query.where(UserDocumentModel.task_id == task_id)
    query = query.order_by(UserDocumentModel.created_at.desc())
    res = await db.execute(query)
    return [DocumentResponse.model_validate(d) for d in res.scalars().all()]

@router.patch("/{document_id}/verify", response_model=DocumentResponse)
async def verify_and_correct_document(
    document_id: str,
    correction: DocumentCorrectionRequest,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(UserDocumentModel)
        .where(UserDocumentModel.id == document_id, UserDocumentModel.user_id == current_user.id)
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.user_corrections = correction.user_corrections
    doc.is_verified_by_user = correction.is_verified
    await db.commit()
    return DocumentResponse.model_validate(doc)

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(UserDocumentModel)
        .where(UserDocumentModel.id == document_id, UserDocumentModel.user_id == current_user.id)
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete physical file
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except OSError:
            pass

    await db.delete(doc)
    await db.commit()
    return {"status": "DELETED", "document_id": document_id}
