# app/api/v1/endpoints/chatbot.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.chatbot import ChatMessageCreate, ChatMessageResponse
from app.utils.ai_client import get_student_chatbot_response
import uuid

router = APIRouter()

# Simulated auth: all users are students (replace later with real auth)
def get_current_user_role() -> str:
    return "student"

@router.post("/chatbot/message/", response_model=ChatMessageResponse)
async def send_message(
    msg: ChatMessageCreate,
    role: str = Depends(get_current_user_role)
):
    if role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only student mode is allowed."
        )

    try:
        bot_reply = await get_student_chatbot_response(msg.message)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e)
        )

    # Generate or reuse conversation ID
    conv_id = msg.conversation_id or str(uuid.uuid4())

    return ChatMessageResponse(
        user_message=msg.message,
        bot_response=bot_reply,
        conversation_id=conv_id
    )