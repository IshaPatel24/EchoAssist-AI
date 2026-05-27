"""
VoiceForge — Omi Integration Service
======================================
Handles:
  1. Omi webhook verification + parsing
  2. Real-time transcript processing
  3. Browser WebSocket voice capture (Omi fallback)

Omi sends POST requests to /api/omi/webhook with transcript segments
every few seconds during active recording sessions.
"""

import os
import hmac
import hashlib
import json
from typing import Optional, Dict

import httpx
from loguru import logger


class OmiService:
    """
    Manages integration with the Omi voice device and app.
    
    Omi App setup:
      1. Create an app at https://omi.me/developers
      2. Set webhook URL to: https://your-domain.com/api/omi/webhook
      3. Copy App ID + Secret to .env
    
    Webhook payload format (from Omi):
    {
      "session_id": "abc123",
      "user_id": "user_xyz",
      "transcript": "Full transcript text here",
      "segments": [
        {"text": "segment text", "speaker": "SPEAKER_0", "start": 0.0, "end": 2.5}
      ]
    }
    """

    def __init__(self):
        self.app_id = os.getenv("OMI_APP_ID", "")
        self.app_secret = os.getenv("OMI_APP_SECRET", "")
        self.webhook_secret = os.getenv("OMI_WEBHOOK_SECRET", "")

    def verify_webhook_signature(self, payload_body: bytes, signature: str) -> bool:
        """
        Verify Omi webhook HMAC signature.
        Omi sends X-Omi-Signature header = HMAC-SHA256(secret, body)
        """
        if not self.webhook_secret:
            logger.warning("OMI_WEBHOOK_SECRET not set — skipping signature verification")
            return True

        expected = hmac.new(
            self.webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def parse_transcript(self, payload: Dict) -> str:
        """
        Extract the best available transcript from an Omi webhook payload.
        Prefers full `transcript` field; falls back to joining segments.
        """
        if payload.get("transcript"):
            return payload["transcript"].strip()

        segments = payload.get("segments", [])
        if segments:
            return " ".join(s.get("text", "") for s in segments).strip()

        return ""

    def build_context_from_segments(self, segments: list) -> str:
        """Format segments with speaker labels for context."""
        if not segments:
            return ""
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "Speaker")
            text = seg.get("text", "")
            if text:
                lines.append(f"{speaker}: {text}")
        return "\n".join(lines)

    async def fetch_omi_memories(self, user_id: str, limit: int = 10) -> list:
        """
        Optionally fetch past Omi memories via the Omi API.
        Requires user to have authenticated your Omi app.
        Returns list of memory objects.
        """
        if not self.app_id or not self.app_secret:
            return []

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.omi.me/v1/memories",
                    headers={
                        "X-App-Id": self.app_id,
                        "X-App-Secret": self.app_secret,
                        "X-User-Id": user_id,
                    },
                    params={"limit": limit},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    return resp.json().get("memories", [])
        except Exception as e:
            logger.error(f"Omi API fetch error: {e}")

        return []
