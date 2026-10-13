"""FastAPI app. Run from the prototype folder:  uvicorn app.main:app --reload"""
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import config
from .assistant import Assistant
from .llm import get_llm

app = FastAPI(title="Harbor & Thread AI Support Assistant (prototype)")
llm = get_llm()
assistant = Assistant(llm)
STATIC = config.PROTOTYPE_DIR / "app" / "static"


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None


class DecisionIn(BaseModel):
    approve: bool
    reason_code: str | None = None


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/config")
def get_config():
    return {"phase": config.PHASE, "provider": config.LLM_PROVIDER,
            "model": config.ANTHROPIC_MODEL if config.LLM_PROVIDER == "anthropic" else "offline keyword model",
            "today": config.TODAY.isoformat()}


@app.post("/api/chat")
def chat(body: ChatIn):
    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Type a message first.")
    if len(message) > 2000:
        raise HTTPException(400, "Messages can be up to 2,000 characters.")
    session_id = body.session_id or uuid.uuid4().hex
    try:
        return assistant.handle(session_id, message)
    except Exception as exc:  # e.g. missing API key or network error
        raise HTTPException(502, f"The AI model couldn't be reached: {exc}") from exc


@app.get("/api/approvals")
def list_approvals():
    return list(assistant.approvals.values())


@app.post("/api/approvals/{approval_id}")
def decide(approval_id: str, body: DecisionIn):
    if approval_id not in assistant.approvals:
        raise HTTPException(404, "No approval with that ID.")
    try:
        return assistant.decide_approval(approval_id, body.approve, body.reason_code)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/test-customers")
def test_customers():
    """Invented test customers, shown in the demo so you can copy their details."""
    return [{"full_name": c["full_name"], "account_id": c["account_id"], "email": c["email"],
             "membership": c["membership"]} for c in assistant.customers.values()]


@app.get("/api/usage")
def usage():
    return getattr(llm, "usage", {})
