"""
VoiceForge — Qdrant Vector Database Service
============================================
Manages all vector storage operations:
  - User preferences (accessibility settings)
  - Document templates
  - Session memory / conversation history
  - Generated document records
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchRequest, UpdateStatus
)
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------------------------
# Collection names
# ---------------------------------------------------------------------------

COLL_PREFERENCES   = "user_preferences"
COLL_TEMPLATES     = "document_templates"
COLL_SESSION       = "session_memory"
COLL_DOCUMENTS     = "generated_docs"

VECTOR_SIZE = 384   # all-MiniLM-L6-v2 output size


# ---------------------------------------------------------------------------
# Default document templates
# ---------------------------------------------------------------------------

DEFAULT_TEMPLATES = [
    {
        "name": "medical_intake",
        "title": "Medical Intake Form",
        "description": "Standard patient intake form for healthcare providers",
        "fields": ["full_name", "date_of_birth", "address", "phone",
                   "emergency_contact", "insurance_provider", "primary_complaint",
                   "current_medications", "allergies", "medical_history"],
        "category": "healthcare",
    },
    {
        "name": "job_application",
        "title": "Job Application Form",
        "description": "General employment application form",
        "fields": ["full_name", "email", "phone", "address",
                   "position_applied", "work_experience", "education",
                   "skills", "references", "availability"],
        "category": "employment",
    },
    {
        "name": "incident_report",
        "title": "Incident Report",
        "description": "Document an incident or accident",
        "fields": ["reporter_name", "date_of_incident", "location",
                   "description", "witnesses", "injuries", "actions_taken"],
        "category": "administration",
    },
    {
        "name": "meeting_summary",
        "title": "Meeting Summary",
        "description": "Structured meeting notes and action items",
        "fields": ["meeting_title", "date", "attendees", "agenda",
                   "discussion_points", "decisions_made", "action_items", "next_meeting"],
        "category": "productivity",
    },
    {
        "name": "accommodation_request",
        "title": "Disability Accommodation Request",
        "description": "Request for workplace or educational accommodations",
        "fields": ["full_name", "date", "organization", "supervisor_name",
                   "nature_of_disability", "requested_accommodations",
                   "supporting_documentation", "preferred_start_date"],
        "category": "accessibility",
    },
]


class QdrantService:
    """Async Qdrant client wrapper for VoiceForge."""

    def __init__(self):
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        api_key = os.getenv("QDRANT_API_KEY") or None

        self.client = AsyncQdrantClient(host=host, port=port, api_key=api_key)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info(f"Qdrant service init: {host}:{port}")

    def _embed(self, text: str) -> List[float]:
        """Create a dense vector embedding for text."""
        return self.encoder.encode(text, normalize_embeddings=True).tolist()

    # -----------------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------------

    async def initialize_collections(self):
        """Create all required Qdrant collections if they don't exist."""
        existing = {c.name for c in (await self.client.get_collections()).collections}

        for name in [COLL_PREFERENCES, COLL_TEMPLATES, COLL_SESSION, COLL_DOCUMENTS]:
            if name not in existing:
                await self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                )
                logger.info(f"✅ Created Qdrant collection: {name}")
            else:
                logger.debug(f"Collection already exists: {name}")

    async def seed_templates(self):
        """Seed default document templates into Qdrant."""
        for tmpl in DEFAULT_TEMPLATES:
            text = f"{tmpl['title']} {tmpl['description']} {' '.join(tmpl['fields'])}"
            point = PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, tmpl["name"])).replace("-", "")[:16],
                vector=self._embed(text),
                payload={**tmpl, "type": "template"},
            )
            await self.client.upsert(collection_name=COLL_TEMPLATES, points=[point])
        logger.info(f"✅ Seeded {len(DEFAULT_TEMPLATES)} document templates")

    # -----------------------------------------------------------------------
    # User Preferences
    # -----------------------------------------------------------------------

    async def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        results = await self.client.search(
            collection_name=COLL_PREFERENCES,
            query_vector=self._embed(f"preferences for user {user_id}"),
            limit=1,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
        )
        if results:
            return results[0].payload
        return None

    async def save_user_preferences(self, user_id: str, prefs: Dict):
        """Upsert user preferences. Uses deterministic ID from user_id."""
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"prefs_{user_id}")).replace("-", "")[:16]
        text = f"accessibility preferences {user_id} {json.dumps(prefs)}"
        await self.client.upsert(
            collection_name=COLL_PREFERENCES,
            points=[PointStruct(
                id=point_id,
                vector=self._embed(text),
                payload={"user_id": user_id, "preferences": prefs, "updated_at": datetime.utcnow().isoformat()},
            )],
        )

    # -----------------------------------------------------------------------
    # Session Memory
    # -----------------------------------------------------------------------

    async def create_session(self, session_id: str, user_id: str):
        await self.client.upsert(
            collection_name=COLL_SESSION,
            points=[PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"sess_{session_id}")).replace("-", "")[:16],
                vector=self._embed(f"session {session_id} user {user_id}"),
                payload={
                    "session_id": session_id,
                    "user_id": user_id,
                    "messages": [],
                    "created_at": datetime.utcnow().isoformat(),
                },
            )],
        )

    async def add_session_message(self, session_id: str, role: str, content: str, **extra):
        """Append a message to session history and also store as searchable memory."""
        # Upsert individual message for semantic search
        msg_id = str(uuid.uuid4()).replace("-", "")[:16]
        await self.client.upsert(
            collection_name=COLL_SESSION,
            points=[PointStruct(
                id=msg_id,
                vector=self._embed(content),
                payload={
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                    **extra,
                },
            )],
        )

    async def get_session_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        results = await self.client.scroll(
            collection_name=COLL_SESSION,
            scroll_filter=Filter(
                must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))]
            ),
            limit=limit,
            with_payload=True,
        )
        messages = [r.payload for r in results[0] if "role" in r.payload]
        return sorted(messages, key=lambda m: m.get("timestamp", ""))

    async def search_session_memory(self, query: str, user_id: str, limit: int = 5) -> List[Dict]:
        """Semantic search across all session memories for a user."""
        results = await self.client.search(
            collection_name=COLL_SESSION,
            query_vector=self._embed(query),
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ) if user_id else None,
        )
        return [r.payload for r in results]

    # -----------------------------------------------------------------------
    # Document Templates
    # -----------------------------------------------------------------------

    async def search_templates(self, query: str, limit: int = 3) -> List[Dict]:
        """Find the best matching document template for a voice query."""
        results = await self.client.search(
            collection_name=COLL_TEMPLATES,
            query_vector=self._embed(query),
            limit=limit,
        )
        return [r.payload for r in results]

    async def list_templates(self) -> List[Dict]:
        results = await self.client.scroll(
            collection_name=COLL_TEMPLATES,
            limit=50,
            with_payload=True,
        )
        return [r.payload for r in results[0]]

    # -----------------------------------------------------------------------
    # Generated Documents
    # -----------------------------------------------------------------------

    async def save_document_record(self, user_id: str, doc_data: Dict):
        """Store metadata about a generated document for later retrieval."""
        doc_id = doc_data.get("doc_id", str(uuid.uuid4()))
        text = f"{doc_data.get('template_name', '')} {doc_data.get('summary', '')} {user_id}"
        await self.client.upsert(
            collection_name=COLL_DOCUMENTS,
            points=[PointStruct(
                id=doc_id.replace("-", "")[:16],
                vector=self._embed(text),
                payload={"user_id": user_id, **doc_data},
            )],
        )

    async def get_user_documents(self, user_id: str, limit: int = 20) -> List[Dict]:
        results = await self.client.scroll(
            collection_name=COLL_DOCUMENTS,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=limit,
            with_payload=True,
        )
        return [r.payload for r in results[0]]

    async def search_documents(self, query: str, user_id: str, limit: int = 5) -> List[Dict]:
        """Semantic search over a user's document history."""
        results = await self.client.search(
            collection_name=COLL_DOCUMENTS,
            query_vector=self._embed(query),
            limit=limit,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
        )
        return [r.payload for r in results]
