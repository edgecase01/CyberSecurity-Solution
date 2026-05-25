from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    model: str = "cybersec-chatbot-mock-v0"


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    """Dummy cybersecurity chatbot — replace with LLM / RAG pipeline later."""
    user_message = body.message.strip()
    lowered = user_message.lower()

    if any(word in lowered for word in ("phishing", "scam", "suspicious")):
        reply = (
            "Treat the message as suspicious. Do not click links, verify the sender "
            "through a separate channel, and report it to your security team."
        )
    elif any(word in lowered for word in ("password", "credential")):
        reply = (
            "Use a unique passphrase of 14+ characters, enable MFA, and never reuse "
            "passwords across sites. Our Password Analyzer can score ideas locally."
        )
    elif any(word in lowered for word in ("malware", "virus", "attachment")):
        reply = (
            "Do not open unexpected attachments. Scan files with your security tools "
            "and quarantine anything flagged by VirusTotal or your endpoint agent."
        )
    else:
        reply = (
            f"I received your question about “{user_message[:120]}”. "
            "In production I would query threat intel and your scan history. "
            "For now: keep software patched, use MFA, and avoid unknown links."
        )

    return ChatResponse(reply=reply)
