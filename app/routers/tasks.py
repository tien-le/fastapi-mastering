from fastapi import APIRouter

from app.core.tasks import send_simple_message

router = APIRouter()

@router.post("/send-email")
async def send_email(to: str, subject: str, body: str):
	result = await send_simple_message(to=to, subject=subject, body=body)
	return {"status": "sent", "mailgun": result}

