# app/utils/ai_client.py
import os
import httpx
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GOOGLE_GEMINI_API_KEY not found in environment variables")

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"

async def get_student_chatbot_response(prompt: str, timeout: int = 30) -> str:
    """
    Uses Google Gemini Flash (fast & free tier friendly) in student mode.
    Enforces educational, concise, safe responses.
    """
    # Enforce student mode via system-like instruction
    student_instruction = (
        "You are a helpful student assistant. "
        "Answer clearly, simply, and in an educational way. "
        "Keep responses under 3 sentences. "
        "Do not write code unless explicitly asked for basics. "
        "Avoid advanced, sensitive, or non-academic topics."
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{student_instruction}\n\nStudent question: {prompt}"}
                ]
            }
        ],
        "safetySettings": [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(GEMINI_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract text from response
            try:
                candidate = data["candidates"][0]
                if "content" in candidate:
                    part = candidate["content"]["parts"][0]
                    if "text" in part:
                        return part["text"].strip()
                return "I'm sorry, I can't answer that in student mode."
            except (KeyError, IndexError):
                return "I'm having trouble understanding your question."

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RuntimeError("Too many requests. Please try again later.")
            elif e.response.status_code == 400:
                raise RuntimeError("Invalid input. Please rephrase your question.")
            else:
                raise RuntimeError(f"AI service error: {e.response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error: {str(e)}")