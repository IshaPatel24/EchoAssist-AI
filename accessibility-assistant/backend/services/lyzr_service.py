"""
VoiceForge — Lyzr AI Service
==============================
Wraps the Lyzr SDK / API for:
  - Intent classification
  - Natural language reasoning
  - Document field extraction
  - Workflow orchestration
  - Response generation

Uses lyzr-automata for multi-agent pipelines.
Falls back to direct OpenAI if Lyzr API key not set (dev mode).
"""

import os
import json
import re
from typing import Optional, Dict, Any, List

import openai
from loguru import logger


# Try importing Lyzr; fall back gracefully
try:
    from lyzr_automata import Agent, Task
    from lyzr_automata.ai_models.openai import OpenAIModel
    from lyzr_automata.pipelines.linear_sync_pipeline import LinearSyncPipeline
    LYZR_AVAILABLE = True
except ImportError:
    LYZR_AVAILABLE = False
    logger.warning("lyzr-automata not installed — using direct OpenAI fallback")


INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a voice-driven accessibility assistant.
Classify the user's voice command into exactly one of these intents:
  - create_document: user wants to generate a document, report, letter, or PDF
  - fill_form: user wants to fill out a specific form (medical, job, etc.)
  - summarize: user wants a summary of past content, meetings, or documents
  - guided_workflow: user wants step-by-step guidance through a multi-step task
  - remember_preference: user wants to save an accessibility preference
  - read_back: user wants text read aloud
  - search_memory: user wants to find past information
  - general_query: general question or conversation
  - unknown: cannot determine intent

Respond ONLY with valid JSON:
{
  "intent": "<intent_name>",
  "confidence": 0.0-1.0,
  "extracted_entities": {
    "template_name": "<if applicable>",
    "subject": "<main topic>",
    "preference_key": "<if remember_preference>",
    "preference_value": "<if remember_preference>"
  }
}
"""

EXTRACTION_SYSTEM_PROMPT = """
You are a data extraction agent for an accessibility document assistant.
The user has spoken a voice command. Extract field values for the requested document.
Return ONLY valid JSON mapping field names to extracted values.
If a value was not mentioned, set it to null.
Be lenient and infer reasonable values from context.
"""

RESPONSE_SYSTEM_PROMPT = """
You are a warm, helpful, accessibility-first AI assistant named VoiceForge.
You help people with disabilities generate documents and complete workflows through voice.
Keep responses concise, clear, and encouraging.
Use simple language. Avoid jargon.
When a document has been created, confirm clearly and describe next steps.
"""


class LyzrService:
    """Multi-agent reasoning via Lyzr (with OpenAI fallback)."""

    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        self.lyzr_key = os.getenv("LYZR_API_KEY")

        if LYZR_AVAILABLE and self.lyzr_key:
            self._init_lyzr_agents()
            logger.info("Lyzr agents initialized")
        else:
            logger.info("Using OpenAI direct mode (Lyzr fallback)")

    def _init_lyzr_agents(self):
        """Initialize Lyzr agent pipeline."""
        self.ai_model = OpenAIModel(
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={"model": "gpt-4o-mini", "temperature": 0.3},
        )
        self.intent_agent = Agent(
            role="Intent Classifier",
            prompt_persona=INTENT_SYSTEM_PROMPT,
        )
        self.extraction_agent = Agent(
            role="Data Extractor",
            prompt_persona=EXTRACTION_SYSTEM_PROMPT,
        )
        self.response_agent = Agent(
            role="Response Generator",
            prompt_persona=RESPONSE_SYSTEM_PROMPT,
        )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def classify_intent(self, transcript: str, context: List[str] = None) -> Dict:
        """Classify the intent of a voice command."""
        context_str = "\n".join(context or [])
        prompt = f"Context:\n{context_str}\n\nUser command: {transcript}"

        if LYZR_AVAILABLE and self.lyzr_key:
            return await self._lyzr_classify(prompt)
        return await self._openai_classify(prompt)

    async def extract_fields(self, transcript: str, template_fields: List[str], existing_data: Dict = None) -> Dict:
        """Extract document field values from speech."""
        fields_str = ", ".join(template_fields)
        existing_str = json.dumps(existing_data or {})
        prompt = (
            f"Fields needed: {fields_str}\n"
            f"Already collected: {existing_str}\n"
            f"User said: {transcript}\n\n"
            f"Extract any field values from what the user said."
        )

        if LYZR_AVAILABLE and self.lyzr_key:
            return await self._lyzr_extract(prompt, template_fields)
        return await self._openai_extract(prompt, template_fields)

    async def generate_response(self, situation: str, context: List[str] = None,
                                 user_prefs: Dict = None) -> str:
        """Generate a natural language response for the user."""
        ctx = "\n".join(context or [])
        prefs = json.dumps(user_prefs or {})
        prompt = (
            f"Situation: {situation}\n"
            f"User preferences: {prefs}\n"
            f"Context: {ctx}"
        )

        if LYZR_AVAILABLE and self.lyzr_key:
            return await self._lyzr_respond(prompt)
        return await self._openai_respond(prompt)

    async def generate_document_content(self, template: Dict, field_values: Dict,
                                         user_prefs: Dict = None) -> str:
        """Generate the text content for a document given template + data."""
        prompt = (
            f"Generate a professional, well-formatted document.\n"
            f"Template: {template.get('title', 'Document')}\n"
            f"Description: {template.get('description', '')}\n"
            f"Fields and values:\n{json.dumps(field_values, indent=2)}\n\n"
            f"Format it clearly with sections and labels. Be thorough and professional."
        )
        return await self._openai_chat(RESPONSE_SYSTEM_PROMPT, prompt)

    async def summarize_content(self, content: str, style: str = "concise") -> str:
        """Summarize text content."""
        prompt = f"Summarize the following in a {style}, accessible way:\n\n{content}"
        return await self._openai_chat(RESPONSE_SYSTEM_PROMPT, prompt)

    # -----------------------------------------------------------------------
    # Lyzr implementation
    # -----------------------------------------------------------------------

    async def _lyzr_classify(self, prompt: str) -> Dict:
        try:
            task = Task(
                name="classify_intent",
                model=self.ai_model,
                agent=self.intent_agent,
                instructions=prompt,
            )
            pipeline = LinearSyncPipeline(tasks=[task], completion_message="done")
            result = pipeline.run()
            output = result[-1]["task_output"] if result else "{}"
            return self._parse_json_safe(output)
        except Exception as e:
            logger.error(f"Lyzr classify error: {e}")
            return await self._openai_classify(prompt)

    async def _lyzr_extract(self, prompt: str, fields: List[str]) -> Dict:
        try:
            task = Task(
                name="extract_fields",
                model=self.ai_model,
                agent=self.extraction_agent,
                instructions=prompt,
            )
            pipeline = LinearSyncPipeline(tasks=[task], completion_message="done")
            result = pipeline.run()
            output = result[-1]["task_output"] if result else "{}"
            return self._parse_json_safe(output)
        except Exception as e:
            logger.error(f"Lyzr extract error: {e}")
            return await self._openai_extract(prompt, fields)

    async def _lyzr_respond(self, prompt: str) -> str:
        try:
            task = Task(
                name="generate_response",
                model=self.ai_model,
                agent=self.response_agent,
                instructions=prompt,
            )
            pipeline = LinearSyncPipeline(tasks=[task], completion_message="done")
            result = pipeline.run()
            return result[-1]["task_output"] if result else "I'm here to help."
        except Exception as e:
            logger.error(f"Lyzr respond error: {e}")
            return await self._openai_respond(prompt)

    # -----------------------------------------------------------------------
    # OpenAI fallback implementation
    # -----------------------------------------------------------------------

    async def _openai_classify(self, prompt: str) -> Dict:
        response = await self._openai_chat_async(INTENT_SYSTEM_PROMPT, prompt)
        return self._parse_json_safe(response)

    async def _openai_extract(self, prompt: str, fields: List[str]) -> Dict:
        fields_hint = f"Return JSON with these keys: {fields}"
        response = await self._openai_chat_async(
            EXTRACTION_SYSTEM_PROMPT + "\n" + fields_hint, prompt
        )
        return self._parse_json_safe(response)

    async def _openai_respond(self, prompt: str) -> str:
        return await self._openai_chat_async(RESPONSE_SYSTEM_PROMPT, prompt)

    async def _openai_chat_async(self, system: str, user: str) -> str:
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return resp.choices[0].message.content.strip()

    def _openai_chat(self, system: str, user: str) -> str:
        """Sync version for non-async contexts."""
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        return resp.choices[0].message.content.strip()

    def _parse_json_safe(self, text: str) -> Dict:
        """Extract JSON from text, handling markdown code blocks."""
        text = re.sub(r"```json\s*|\s*```", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return {}
