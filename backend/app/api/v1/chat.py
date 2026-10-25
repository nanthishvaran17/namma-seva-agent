import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.models.conversation import ConversationModel, MessageModel
from backend.app.core.config import settings
from backend.app.core.rate_limit import RateLimiter
from backend.app.schemas.chat import ChatRequest, ChatResponse, Citation
from backend.app.agent.orchestrator import agent_orchestrator
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/chat", tags=["Conversational AI Assistant"])

chat_rate_limit = Depends(RateLimiter(key_prefix="chat"))

@router.post("", response_model=ChatResponse, dependencies=[chat_rate_limit])
@router.post("/", response_model=ChatResponse, dependencies=[chat_rate_limit])
async def chat_with_agent(
    req: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Resolve or create conversation
    conv_id = req.conversation_id
    if conv_id and current_user:
        res = await db.execute(select(ConversationModel).where(ConversationModel.id == conv_id, ConversationModel.user_id == current_user.id))
        conversation = res.scalar_one_or_none()
        if not conversation:
            conv_id = None

    if not conv_id:
        conv_id = str(uuid.uuid4())
        if current_user:
            conversation = ConversationModel(
                id=conv_id,
                user_id=current_user.id,
                title=req.message[:50],
                channel="WEB"
            )
            db.add(conversation)
            await db.flush()

    # 2. Retrieve history if authenticated
    history = []
    if current_user:
        hist_res = await db.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conv_id)
            .order_by(MessageModel.created_at.asc())
            .limit(10)
        )
        for msg in hist_res.scalars().all():
            history.append({
                "role": "user" if msg.sender == "USER" else "assistant",
                "content": msg.content
            })

    # Add current message
    history.append({"role": "user", "content": req.message})

    # 3. Process via Agent Orchestrator
    user_context = {
        "user_id": current_user.id if current_user else "anonymous",
        "language": req.language or "ta",
        **(req.context or {})
    }
    agent_res = await agent_orchestrator.process_user_message(history, user_context=user_context)

    # 4. Save messages if authenticated
    if current_user:
        user_msg = MessageModel(
            conversation_id=conv_id,
            sender="USER",
            content=req.message,
            language=req.language or "ta",
            metadata_json={}
        )
        db.add(user_msg)

        agent_msg = MessageModel(
            conversation_id=conv_id,
            sender="AGENT",
            content=agent_res.content,
            language=agent_res.language,
            metadata_json={
                "tool_calls": [tc.model_dump() for tc in agent_res.tool_calls],
                "citations": agent_res.citations,
                "action_cards": agent_res.action_cards
            }
        )
        db.add(agent_msg)
        await db.commit()

    return ChatResponse(
        conversation_id=conv_id,
        message=agent_res.content,
        language=agent_res.language,
        citations=[Citation(title=c["title"], url=c["url"]) for c in agent_res.citations],
        action_cards=agent_res.action_cards,
        requires_user_confirmation=agent_res.requires_user_confirmation,
        confirmation_prompt=agent_res.confirmation_prompt
    )

@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return []
    res = await db.execute(
        select(ConversationModel)
        .where(ConversationModel.user_id == current_user.id)
        .order_by(ConversationModel.updated_at.desc())
        .limit(20)
    )
    convs = res.scalars().all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "updated_at": c.updated_at.isoformat()
        }
        for c in convs
    ]

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return []
    res = await db.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at.asc())
    )
    msgs = res.scalars().all()
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "content": m.content,
            "language": m.language,
            "metadata": m.metadata_json,
            "created_at": m.created_at.isoformat()
        }
        for m in msgs
    ]
