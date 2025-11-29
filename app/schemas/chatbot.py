# app/schemas/chatbot.py
from pydantic import BaseModel
from typing import Optional

class ChatMessageCreate(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    user_message: str
    bot_response: str
    conversation_id: str
    mode: str = "student"