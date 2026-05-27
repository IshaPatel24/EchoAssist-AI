"""
VoiceForge — Pydantic Data Models
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class IntentType(str, Enum):
    CREATE_DOCUMENT = "create_document"
    FILL_FORM = "fill_form"
    SUMMARIZE = "summarize"
    GUIDED_WORKFLOW = "guided_workflow"
    REMEMBER_PREFERENCE = "remember_preference"
    READ_BACK = "read_back"
    SEARCH_MEMORY = "search_memory"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"


class OutputType(str, Enum):
    PDF = "pdf"
    TEXT = "text"
    AUDIO = "audio"
    WORKFLOW = "workflow"
    NONE = "none"


# ---------------------------------------------------------------------------
# Omi
# ---------------------------------------------------------------------------

class OmiTranscriptSegment(BaseModel):
    text: str
    speaker: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class OmiWebhookPayload(BaseModel):
    """Payload from Omi device webhook."""
    session_id: str
    user_id: Optional[str] = None
    transcript: str  # Full transcript text
    segments: Optional[List[OmiTranscriptSegment]] = []
    memory_id: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class VoiceCommandRequest(BaseModel):
    transcript: str = Field(..., description="The voice command text")
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"


class VoiceCommandResponse(BaseModel):
    intent: IntentType
    response_text: str
    output_type: OutputType = OutputType.NONE
    output_url: Optional[str] = None
    workflow_step: Optional[int] = None
    workflow_total: Optional[int] = None
    audio_url: Optional[str] = None
    context_used: Optional[List[str]] = []  # snippets retrieved from Qdrant
    session_id: Optional[str] = None


# ---------------------------------------------------------------------------
# User & Preferences
# ---------------------------------------------------------------------------

class UserPreferences(BaseModel):
    font_size: Optional[str] = "medium"       # small | medium | large | x-large
    contrast_mode: Optional[str] = "normal"   # normal | high | dark
    tts_speed: Optional[float] = 1.0          # 0.5 – 2.0
    tts_voice: Optional[str] = "default"
    language: Optional[str] = "en"
    reduce_motion: Optional[bool] = False
    screen_reader_mode: Optional[bool] = False
    preferred_output: Optional[str] = "pdf"   # pdf | text | audio
    custom: Optional[Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    user_id: str = "default_user"


class SessionMessage(BaseModel):
    role: str  # user | assistant
    content: str
    timestamp: Optional[str] = None
    intent: Optional[IntentType] = None
    output_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentRequest(BaseModel):
    template_name: str
    user_id: str
    field_values: Dict[str, Any] = {}
    output_format: str = "pdf"  # pdf | docx


class DocumentRecord(BaseModel):
    doc_id: str
    user_id: str
    template_name: str
    filename: str
    url: str
    created_at: str
    summary: Optional[str] = None


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

class WorkflowStep(BaseModel):
    step_number: int
    title: str
    prompt: str          # What to ask the user
    field_key: str       # Where to store the answer
    required: bool = True
    input_type: str = "voice"  # voice | choice | confirm


class WorkflowState(BaseModel):
    workflow_id: str
    template_name: str
    current_step: int = 0
    total_steps: int = 0
    collected_data: Dict[str, Any] = {}
    steps: List[WorkflowStep] = []
    completed: bool = False
