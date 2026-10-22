from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.models.task import UserTaskModel, TaskEventModel
from backend.app.models.user import User
from backend.app.schemas.task import TaskCreate, TaskStatusUpdate, TaskResponse
from backend.app.api.deps import require_current_user
from backend.app.playbooks.loader import playbook_loader
from backend.app.planning.dependency_graph import DependencyPlanner

router = APIRouter(prefix="/tasks", tags=["Application Tasks & Progress Tracking"])

VALID_STATES = {
    "DRAFT",
    "NEEDS_INFORMATION",
    "COLLECTING_DOCUMENTS",
    "READY_FOR_USER_REVIEW",
    "READY_TO_SUBMIT",
    "SUBMITTED",
    "TRACKING",
    "COMPLETED",
    "BLOCKED",
    "REJECTED",
    "CANCELLED"
}

ALLOWED_TRANSITIONS = {
    "DRAFT": {"NEEDS_INFORMATION", "COLLECTING_DOCUMENTS", "CANCELLED"},
    "NEEDS_INFORMATION": {"COLLECTING_DOCUMENTS", "CANCELLED"},
    "COLLECTING_DOCUMENTS": {"READY_FOR_USER_REVIEW", "READY_TO_SUBMIT", "BLOCKED", "CANCELLED"},
    "READY_FOR_USER_REVIEW": {"READY_TO_SUBMIT", "COLLECTING_DOCUMENTS", "CANCELLED"},
    "READY_TO_SUBMIT": {"SUBMITTED", "COMPLETED", "READY_FOR_USER_REVIEW", "CANCELLED"},
    "SUBMITTED": {"TRACKING", "COMPLETED", "REJECTED"},
    "TRACKING": {"COMPLETED", "REJECTED", "BLOCKED"},
    "BLOCKED": {"COLLECTING_DOCUMENTS", "CANCELLED"},
    "REJECTED": {"DRAFT", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set()
}

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_user_task(
    task_in: TaskCreate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = playbook_loader.get_service(task_in.service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{task_in.service_id}' does not exist.")

    # Generate personalized plan
    planner = DependencyPlanner(playbook_loader.catalog)
    plan = planner.generate_action_plan(target_service_id=task_in.service_id)

    new_task = UserTaskModel(
        user_id=current_user.id,
        service_id=task_in.service_id,
        status="COLLECTING_DOCUMENTS" if service.get("required_documents") else "READY_FOR_USER_REVIEW",
        action_plan=plan,
        form_data={},
        submission_evidence={},
        next_action_en=f"Prepare and upload mandatory documents for {service.get('name_en')}",
        next_action_ta=f"{service.get('name_ta')} விண்ணப்பிக்க தேவையான ஆவணங்களை தயார் செய்து பதிவேற்றவும்",
        target_deadline=task_in.target_deadline
    )
    db.add(new_task)
    await db.flush()

    # Record initial event
    event = TaskEventModel(
        task_id=new_task.id,
        previous_status=None,
        new_status=new_task.status,
        reason="Citizen initiated new service task",
        metadata_json={"service_name": service.get("name_en")}
    )
    db.add(event)
    await db.commit()

    return TaskResponse.model_validate(new_task)

@router.get("", response_model=List[TaskResponse])
async def list_user_tasks(
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(UserTaskModel)
        .where(UserTaskModel.user_id == current_user.id)
        .order_by(UserTaskModel.updated_at.desc())
    )
    return [TaskResponse.model_validate(t) for t in res.scalars().all()]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_details(
    task_id: str,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(UserTaskModel)
        .where(UserTaskModel.id == task_id, UserTaskModel.user_id == current_user.id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied.")
    return TaskResponse.model_validate(task)

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: str,
    update_data: TaskStatusUpdate,
    current_user: User = Depends(require_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(UserTaskModel)
        .where(UserTaskModel.id == task_id, UserTaskModel.user_id == current_user.id)
    )
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or access denied.")

    target_status = update_data.status
    if target_status not in VALID_STATES:
        raise HTTPException(status_code=400, detail=f"Invalid state '{target_status}'.")

    # Validate state transition
    allowed = ALLOWED_TRANSITIONS.get(task.status, set())
    if target_status not in allowed and target_status != task.status:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition task from '{task.status}' to '{target_status}'. Allowed: {sorted(list(allowed))}"
        )

    prev_status = task.status
    task.status = target_status

    if update_data.step_index is not None:
        task.current_step_index = update_data.step_index
    if update_data.form_data:
        task.form_data = {**task.form_data, **update_data.form_data}
    if update_data.submission_evidence:
        task.submission_evidence = {**task.submission_evidence, **update_data.submission_evidence}

    event = TaskEventModel(
        task_id=task.id,
        previous_status=prev_status,
        new_status=target_status,
        reason=update_data.reason or "Citizen progress update",
        metadata_json={"updated_by": current_user.email}
    )
    db.add(event)
    await db.commit()

    return TaskResponse.model_validate(task)
