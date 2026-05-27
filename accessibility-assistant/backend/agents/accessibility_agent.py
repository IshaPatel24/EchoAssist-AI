"""
VoiceForge — Accessibility Agent (Main Orchestrator)
=====================================================
The central Lyzr-powered agent that:
  1. Receives voice transcripts (from Omi or WebSocket)
  2. Classifies intent using Lyzr
  3. Retrieves relevant memory/templates from Qdrant
  4. Routes to specialized sub-agents
  5. Generates structured outputs (PDF, audio, workflows)
  6. Stores results back in Qdrant for persistent memory
"""

import uuid
from datetime import datetime
from typing import Optional

from loguru import logger

from models.schemas import VoiceCommandResponse, IntentType, OutputType
from services.qdrant_service import QdrantService
from services.lyzr_service import LyzrService
from services.tts_service import TTSService
from services.document_service import DocumentService
from agents.workflow_agent import WorkflowAgent


class AccessibilityAgent:
    """
    Central orchestrator. Processes every voice command end-to-end.
    
    Pipeline:
      voice → intent classification → memory retrieval
           → route to sub-agent → generate output
           → TTS feedback → store memory → return result
    """

    def __init__(self, qdrant: QdrantService, lyzr: LyzrService,
                 tts: TTSService, docs: DocumentService):
        self.qdrant = qdrant
        self.lyzr = lyzr
        self.tts = tts
        self.docs = docs
        self.workflow_agent = WorkflowAgent(qdrant, lyzr, docs)

        # In-memory workflow state per session
        # (for multi-turn guided workflows)
        self._active_workflows: dict = {}

    async def process_voice_input(self, transcript: str, session_id: str,
                                   user_id: str) -> VoiceCommandResponse:
        """
        Main entry point. Process a voice transcript and return structured response.
        """
        logger.info(f"Processing: '{transcript[:60]}...' | session={session_id}")

        # 1. Load user preferences from Qdrant
        user_prefs_data = await self.qdrant.get_user_preferences(user_id) or {}
        user_prefs = user_prefs_data.get("preferences", {})

        # 2. Retrieve recent session context for RAG
        context_items = await self.qdrant.search_session_memory(transcript, user_id, limit=3)
        context = [item.get("content", "") for item in context_items if item.get("content")]

        # 3. Check if this session has an active workflow
        if session_id in self._active_workflows:
            return await self._continue_workflow(session_id, transcript, user_id, user_prefs)

        # 4. Classify intent via Lyzr
        intent_data = await self.lyzr.classify_intent(transcript, context)
        intent_str = intent_data.get("intent", "unknown")
        entities = intent_data.get("extracted_entities", {})

        logger.info(f"Intent: {intent_str} | confidence={intent_data.get('confidence', 0):.2f}")

        # Map intent string to enum
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN

        # 5. Store user message in session memory
        await self.qdrant.add_session_message(
            session_id=session_id,
            role="user",
            content=transcript,
            user_id=user_id,
            intent=intent.value,
        )

        # 6. Route to appropriate handler
        result = await self._route_intent(
            intent=intent,
            transcript=transcript,
            entities=entities,
            session_id=session_id,
            user_id=user_id,
            user_prefs=user_prefs,
            context=context,
        )

        # 7. Generate TTS audio response (if user prefers audio or screen reader mode)
        if user_prefs.get("screen_reader_mode") or user_prefs.get("preferred_output") == "audio":
            if result.response_text:
                audio_url = await self.tts.synthesize(
                    result.response_text,
                    speed=float(user_prefs.get("tts_speed", 1.0)),
                    language=user_prefs.get("language", "en"),
                )
                result.audio_url = audio_url

        # 8. Store assistant response in memory
        await self.qdrant.add_session_message(
            session_id=session_id,
            role="assistant",
            content=result.response_text,
            user_id=user_id,
            output_type=result.output_type.value,
            output_url=result.output_url or "",
        )

        result.session_id = session_id
        return result

    # -----------------------------------------------------------------------
    # Intent Router
    # -----------------------------------------------------------------------

    async def _route_intent(self, intent: IntentType, transcript: str,
                             entities: dict, session_id: str, user_id: str,
                             user_prefs: dict, context: list) -> VoiceCommandResponse:

        if intent == IntentType.CREATE_DOCUMENT:
            return await self._handle_create_document(transcript, entities, user_id, user_prefs)

        elif intent == IntentType.FILL_FORM:
            return await self._handle_fill_form(transcript, entities, session_id, user_id, user_prefs)

        elif intent == IntentType.SUMMARIZE:
            return await self._handle_summarize(transcript, user_id, context)

        elif intent == IntentType.GUIDED_WORKFLOW:
            return await self._start_workflow(transcript, entities, session_id, user_id, user_prefs)

        elif intent == IntentType.REMEMBER_PREFERENCE:
            return await self._handle_remember_preference(entities, user_id)

        elif intent == IntentType.READ_BACK:
            return await self._handle_read_back(transcript, user_id, user_prefs)

        elif intent == IntentType.SEARCH_MEMORY:
            return await self._handle_search_memory(transcript, user_id)

        else:
            return await self._handle_general(transcript, context, user_prefs)

    # -----------------------------------------------------------------------
    # Handlers
    # -----------------------------------------------------------------------

    async def _handle_create_document(self, transcript: str, entities: dict,
                                       user_id: str, user_prefs: dict) -> VoiceCommandResponse:
        """Create a structured document from voice command."""
        # Find best matching template
        templates = await self.qdrant.search_templates(transcript, limit=1)
        if not templates:
            return VoiceCommandResponse(
                intent=IntentType.CREATE_DOCUMENT,
                response_text="I couldn't find a matching document template. Could you describe what kind of document you need?",
                output_type=OutputType.NONE,
            )

        template = templates[0]
        logger.info(f"Using template: {template['name']}")

        # Extract field values from the transcript
        fields = template.get("fields", [])
        field_values = await self.lyzr.extract_fields(transcript, fields)

        # Generate AI document content
        ai_content = await self.lyzr.generate_document_content(template, field_values, user_prefs)

        # Generate PDF
        filename = await self.docs.generate_pdf(template, field_values, ai_content, user_prefs)
        if not filename:
            return VoiceCommandResponse(
                intent=IntentType.CREATE_DOCUMENT,
                response_text="I encountered an error generating your document. Please try again.",
                output_type=OutputType.NONE,
            )

        doc_url = f"/docs-output/{filename}"

        # Save to Qdrant memory
        await self.qdrant.save_document_record(user_id, {
            "doc_id": str(uuid.uuid4()),
            "template_name": template["name"],
            "filename": filename,
            "url": doc_url,
            "created_at": datetime.utcnow().isoformat(),
            "summary": f"{template['title']} for {field_values.get('full_name', 'user')}",
            "field_values": field_values,
        })

        response_text = (
            f"I've created your {template['title']}. "
            f"The document is ready to download. "
            f"It includes {len([v for v in field_values.values() if v and v != 'null'])} filled fields."
        )

        return VoiceCommandResponse(
            intent=IntentType.CREATE_DOCUMENT,
            response_text=response_text,
            output_type=OutputType.PDF,
            output_url=doc_url,
        )

    async def _handle_fill_form(self, transcript: str, entities: dict,
                                 session_id: str, user_id: str, user_prefs: dict) -> VoiceCommandResponse:
        """Start a guided form-filling workflow."""
        # Reuse guided workflow logic
        return await self._start_workflow(transcript, entities, session_id, user_id, user_prefs)

    async def _start_workflow(self, transcript: str, entities: dict,
                               session_id: str, user_id: str, user_prefs: dict) -> VoiceCommandResponse:
        """Initialize a guided multi-step workflow."""
        templates = await self.qdrant.search_templates(transcript, limit=1)
        if not templates:
            return VoiceCommandResponse(
                intent=IntentType.GUIDED_WORKFLOW,
                response_text="I couldn't find a matching form or workflow. What would you like to complete?",
                output_type=OutputType.NONE,
            )

        template = templates[0]
        workflow_state = self.workflow_agent.create_workflow(template)
        self._active_workflows[session_id] = workflow_state

        first_step = self.workflow_agent.get_current_step(workflow_state)
        response_text = (
            f"Let's complete your {template['title']} together. "
            f"This has {workflow_state.total_steps} steps. "
            f"Step 1 of {workflow_state.total_steps}: {first_step.prompt}"
        )

        return VoiceCommandResponse(
            intent=IntentType.GUIDED_WORKFLOW,
            response_text=response_text,
            output_type=OutputType.WORKFLOW,
            workflow_step=1,
            workflow_total=workflow_state.total_steps,
        )

    async def _continue_workflow(self, session_id: str, transcript: str,
                                  user_id: str, user_prefs: dict) -> VoiceCommandResponse:
        """Continue an active multi-step workflow."""
        workflow_state = self._active_workflows[session_id]
        result = await self.workflow_agent.process_step(workflow_state, transcript)

        if result.get("completed"):
            # Generate final document
            del self._active_workflows[session_id]
            template = result["template"]
            field_values = result["collected_data"]

            ai_content = await self.lyzr.generate_document_content(template, field_values, user_prefs)
            filename = await self.docs.generate_pdf(template, field_values, ai_content, user_prefs)
            doc_url = f"/docs-output/{filename}" if filename else None

            if filename:
                await self.qdrant.save_document_record(user_id, {
                    "doc_id": str(uuid.uuid4()),
                    "template_name": template["name"],
                    "filename": filename,
                    "url": doc_url,
                    "created_at": datetime.utcnow().isoformat(),
                    "summary": f"Completed {template['title']}",
                    "field_values": field_values,
                })

            return VoiceCommandResponse(
                intent=IntentType.GUIDED_WORKFLOW,
                response_text=f"All done! Your {template.get('title', 'document')} is ready to download.",
                output_type=OutputType.PDF,
                output_url=doc_url,
                workflow_step=workflow_state.total_steps,
                workflow_total=workflow_state.total_steps,
            )

        next_step = result["next_step"]
        current = result["current_step"]
        total = workflow_state.total_steps

        return VoiceCommandResponse(
            intent=IntentType.GUIDED_WORKFLOW,
            response_text=f"Got it. Step {current + 1} of {total}: {next_step.prompt}",
            output_type=OutputType.WORKFLOW,
            workflow_step=current + 1,
            workflow_total=total,
        )

    async def _handle_summarize(self, transcript: str, user_id: str,
                                 context: list) -> VoiceCommandResponse:
        """Summarize past documents or meeting notes."""
        # Search for relevant past content
        docs = await self.qdrant.search_documents(transcript, user_id, limit=3)
        memory = await self.qdrant.search_session_memory(transcript, user_id, limit=5)

        content_pieces = []
        for doc in docs:
            content_pieces.append(f"Document: {doc.get('summary', '')} ({doc.get('template_name', '')})")
        for mem in memory:
            if mem.get("role") == "user":
                content_pieces.append(f"Conversation: {mem.get('content', '')}")

        if not content_pieces:
            return VoiceCommandResponse(
                intent=IntentType.SUMMARIZE,
                response_text="I don't have any previous documents or conversations to summarize yet. Try creating a document first!",
                output_type=OutputType.NONE,
            )

        combined = "\n".join(content_pieces)
        summary = await self.lyzr.summarize_content(combined)

        return VoiceCommandResponse(
            intent=IntentType.SUMMARIZE,
            response_text=summary,
            output_type=OutputType.TEXT,
            context_used=[c[:100] for c in content_pieces[:3]],
        )

    async def _handle_remember_preference(self, entities: dict, user_id: str) -> VoiceCommandResponse:
        """Store an accessibility preference in Qdrant."""
        key = entities.get("preference_key", "")
        value = entities.get("preference_value", "")

        if not key or not value:
            return VoiceCommandResponse(
                intent=IntentType.REMEMBER_PREFERENCE,
                response_text="I heard you want to save a preference, but I'm not sure what. Could you say something like: 'Remember I prefer large text' or 'Set high contrast mode'?",
                output_type=OutputType.NONE,
            )

        prefs_data = await self.qdrant.get_user_preferences(user_id) or {}
        prefs = prefs_data.get("preferences", {})
        prefs[key] = value
        await self.qdrant.save_user_preferences(user_id, prefs)

        return VoiceCommandResponse(
            intent=IntentType.REMEMBER_PREFERENCE,
            response_text=f"I've remembered your preference: {key.replace('_', ' ')} is now set to {value}. This will be applied to all future documents and interactions.",
            output_type=OutputType.NONE,
        )

    async def _handle_read_back(self, transcript: str, user_id: str,
                                 user_prefs: dict) -> VoiceCommandResponse:
        """Read back the most recent document or content."""
        docs = await self.qdrant.get_user_documents(user_id, limit=1)
        if not docs:
            text = "You don't have any recent documents. Try asking me to create one!"
        else:
            doc = docs[0]
            text = f"Your most recent document is a {doc.get('template_name', 'document')} created on {doc.get('created_at', 'recently')}. {doc.get('summary', '')}"

        audio_url = await self.tts.synthesize(
            text,
            speed=float(user_prefs.get("tts_speed", 1.0)),
            language=user_prefs.get("language", "en"),
        )

        return VoiceCommandResponse(
            intent=IntentType.READ_BACK,
            response_text=text,
            output_type=OutputType.AUDIO,
            audio_url=audio_url,
        )

    async def _handle_search_memory(self, transcript: str, user_id: str) -> VoiceCommandResponse:
        """Search past documents and conversations."""
        docs = await self.qdrant.search_documents(transcript, user_id, limit=3)
        memories = await self.qdrant.search_session_memory(transcript, user_id, limit=3)

        results = []
        for doc in docs:
            results.append(f"• Document: {doc.get('summary', doc.get('template_name', 'Unknown'))}")
        for mem in memories:
            if mem.get("role") == "user" and mem.get("content"):
                results.append(f"• Conversation: {mem['content'][:100]}...")

        if not results:
            response_text = "I couldn't find anything matching that in your history."
        else:
            response_text = "Here's what I found:\n" + "\n".join(results[:5])

        return VoiceCommandResponse(
            intent=IntentType.SEARCH_MEMORY,
            response_text=response_text,
            output_type=OutputType.TEXT,
            context_used=results[:3],
        )

    async def _handle_general(self, transcript: str, context: list,
                               user_prefs: dict) -> VoiceCommandResponse:
        """Handle general questions and conversation."""
        situation = f"User said: {transcript}\nProvide a helpful response."
        response_text = await self.lyzr.generate_response(situation, context, user_prefs)

        return VoiceCommandResponse(
            intent=IntentType.GENERAL_QUERY,
            response_text=response_text,
            output_type=OutputType.TEXT,
        )
