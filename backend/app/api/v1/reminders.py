from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.db.session import get_db
from backend.app.models.reminder import ReminderModel
from backend.app.models.user import User
from backend.app.schemas.reminder import ReminderCreate, ReminderResponse
from backend.app.api.deps import require_current_user

router = APIRouter(prefix="/reminders", tags=["Reminders & Notifications"])

@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_in: ReminderCreate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    reminder = ReminderModel(
        user_id=current_user.id,
        task_id=reminder_in.task_id,
        title_en=reminder_in.title_en,
        title_ta=reminder_in.title_ta,
        message_en=reminder_in.message_en,
        message_ta=reminder_in.message_ta,
        scheduled_for=reminder_in.scheduled_for,
        channel=reminder_in.channel,
        status="SCHEDULED"
    )
    db.add(reminder)
    await db.commit()
    return ReminderResponse.model_validate(reminder)

@router.get("", response_model=List[ReminderResponse])
async def list_reminders(
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(ReminderModel)
        .where(ReminderModel.user_id == current_user.id)
        .order_by(ReminderModel.scheduled_for.asc())
    )
    return [ReminderResponse.model_validate(r) for r in res.scalars().all()]

@router.patch("/{reminder_id}/cancel", response_model=ReminderResponse)
async def cancel_reminder(
    reminder_id: str,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(ReminderModel)
        .where(ReminderModel.id == reminder_id, ReminderModel.user_id == current_user.id)
    )
    reminder = res.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")

    reminder.status = "CANCELLED"
    await db.commit()
    return ReminderResponse.model_validate(reminder)
