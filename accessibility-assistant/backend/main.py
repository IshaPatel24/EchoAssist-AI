"""
VoiceForge Accessibility Assistant — FastAPI Backend
=====================================================
Main application entry point. Wires together:
  - Omi webhook + WebSocket voice receiver
  - Lyzr agent orchestration
  - Qdrant vector memory
  - Document generation endpoints
"""

import os
import uuid
import asyncio
from contextlib import asynccontextmanager
from loguru import logger

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models.schemas import (
    OmiWebhookPayload, VoiceCommandRequest, VoiceCommandResponse,
    UserPreferences, SessionCreate, DocumentRequest
)
from services.omi_service import OmiService
from services.qdrant_service import QdrantService
from services.lyzr_service import LyzrService
from services.tts_service import TTSService
from services.document_service import DocumentService
from agents.accessibility_agent import AccessibilityAgent

# ---------------------------------------------------------------------------
# App Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup."""
    logger.info("🚀 VoiceForge starting up...")

    # Initialize Qdrant collections
    qdrant = QdrantService()
    await qdrant.initialize_collections()
    app.state.qdrant = qdrant

    # Seed default document templates into Qdrant
    await qdrant.seed_templates()

    # Initialize services
    app.state.omi = OmiService()
    app.state.lyzr = LyzrService()
    app.state.tts = TTSService()
    app.state.docs = DocumentService()

    # Initialize main agent
    app.state.agent = AccessibilityAgent(
        qdrant=qdrant,
        lyzr=app.state.lyzr,
        tts=app.state.tts,
        docs=app.state.docs,
    )

    # Create output directory
    os.makedirs("generated_docs", exist_ok=True)

    logger.info("✅ All services initialized.")
    yield

    logger.info("🛑 VoiceForge shutting down...")


# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VoiceForge Accessibility Assistant",
    description="Voice-driven accessibility assistant using Omi + Qdrant + Lyzr",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated documents
app.mount("/docs-output", StaticFiles(directory="generated_docs"), name="docs-output")


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def get_agent(request) -> AccessibilityAgent:
    return request.app.state.agent

def get_qdrant(request) -> QdrantService:
    return request.app.state.qdrant


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "VoiceForge", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Omi Webhook — receives real-time transcripts from Omi device
# ---------------------------------------------------------------------------

@app.post("/api/omi/webhook", tags=["Omi"])
async def omi_webhook(
    payload: OmiWebhookPayload,
    background_tasks: BackgroundTasks,
    request=None,
):
    """
    Omi posts memory/transcript segments here in real time.
    We extract intent and trigger the appropriate agent workflow.
    """
    logger.info(f"📡 Omi webhook received: session={payload.session_id}")

    agent: AccessibilityAgent = app.state.agent

    # Process in background so we return 200 quickly to Omi
    background_tasks.add_task(
        agent.process_voice_input,
        transcript=payload.transcript,
        session_id=payload.session_id,
        user_id=payload.user_id or "default_user",
    )

    return {"status": "received", "session_id": payload.session_id}


# ---------------------------------------------------------------------------
# WebSocket — real-time browser voice streaming (non-Omi fallback)
# ---------------------------------------------------------------------------

@app.websocket("/ws/voice/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """
    Browser sends audio chunks over WebSocket.
    Server streams back agent responses + structured outputs.
    """
    await websocket.accept()
    agent: AccessibilityAgent = app.state.agent
    omi: OmiService = app.state.omi

    logger.info(f"🔌 WebSocket connected: session={session_id}")

    try:
        while True:
            # Receive audio chunk or text transcript from browser
            data = await websocket.receive_json()

            msg_type = data.get("type", "transcript")

            if msg_type == "transcript":
                # Browser already did STT (Web Speech API), sends text
                transcript = data.get("text", "")
                user_id = data.get("user_id", "browser_user")

                if not transcript.strip():
                    continue

                logger.info(f"🎙️ Transcript: {transcript[:80]}")

                # Stream back: typing indicator
                await websocket.send_json({"type": "thinking", "message": "Processing your request..."})

                # Run agent
                result = await agent.process_voice_input(
                    transcript=transcript,
                    session_id=session_id,
                    user_id=user_id,
                )

                # Send result back
                await websocket.send_json({
                    "type": "response",
                    "intent": result.intent,
                    "response_text": result.response_text,
                    "output_type": result.output_type,
                    "output_url": result.output_url,
                    "workflow_step": result.workflow_step,
                    "workflow_total": result.workflow_total,
                    "audio_url": result.audio_url,
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


# ---------------------------------------------------------------------------
# REST API — Voice Command (for testing / non-WS clients)
# ---------------------------------------------------------------------------

@app.post("/api/command", response_model=VoiceCommandResponse, tags=["Commands"])
async def process_command(body: VoiceCommandRequest):
    """Process a text/voice command and return structured output."""
    agent: AccessibilityAgent = app.state.agent

    result = await agent.process_voice_input(
        transcript=body.transcript,
        session_id=body.session_id or str(uuid.uuid4()),
        user_id=body.user_id or "api_user",
    )
    return result


# ---------------------------------------------------------------------------
# User Preferences
# ---------------------------------------------------------------------------

@app.get("/api/preferences/{user_id}", tags=["Preferences"])
async def get_preferences(user_id: str):
    """Retrieve stored accessibility preferences for a user."""
    qdrant: QdrantService = app.state.qdrant
    prefs = await qdrant.get_user_preferences(user_id)
    return prefs or {"user_id": user_id, "preferences": {}}


@app.post("/api/preferences/{user_id}", tags=["Preferences"])
async def save_preferences(user_id: str, prefs: UserPreferences):
    """Save / update accessibility preferences for a user."""
    qdrant: QdrantService = app.state.qdrant
    await qdrant.save_user_preferences(user_id, prefs.dict())
    return {"status": "saved", "user_id": user_id}


# ---------------------------------------------------------------------------
# Document endpoints
# ---------------------------------------------------------------------------

@app.get("/api/documents/{user_id}", tags=["Documents"])
async def list_documents(user_id: str):
    """List all generated documents for a user (from Qdrant memory)."""
    qdrant: QdrantService = app.state.qdrant
    docs = await qdrant.get_user_documents(user_id, limit=20)
    return {"documents": docs}


@app.get("/api/documents/download/{filename}", tags=["Documents"])
async def download_document(filename: str):
    """Download a generated document by filename."""
    path = f"generated_docs/{filename}"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(path, filename=filename)


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

@app.post("/api/session", tags=["Session"])
async def create_session(body: SessionCreate):
    """Create a new session and return session_id."""
    session_id = str(uuid.uuid4())
    qdrant: QdrantService = app.state.qdrant
    await qdrant.create_session(session_id, body.user_id)
    return {"session_id": session_id}


@app.get("/api/session/{session_id}/history", tags=["Session"])
async def get_session_history(session_id: str):
    """Get conversation history for a session."""
    qdrant: QdrantService = app.state.qdrant
    history = await qdrant.get_session_history(session_id)
    return {"session_id": session_id, "history": history}


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@app.get("/api/templates", tags=["Templates"])
async def list_templates():
    """List all available document templates."""
    qdrant: QdrantService = app.state.qdrant
    templates = await qdrant.list_templates()
    return {"templates": templates}
