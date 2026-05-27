"""
VoiceForge — Text-to-Speech Service
=====================================
Generates audio feedback for accessibility.
Primary: ElevenLabs (high quality, natural voice)
Fallback: gTTS (Google TTS, free)
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional

from loguru import logger


OUTPUT_DIR = Path("generated_docs/audio")


class TTSService:
    """Convert text to speech audio files."""

    def __init__(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

        if self.elevenlabs_key:
            try:
                from elevenlabs import ElevenLabs
                self.el_client = ElevenLabs(api_key=self.elevenlabs_key)
                self.use_elevenlabs = True
                logger.info("TTS: ElevenLabs enabled")
            except ImportError:
                self.use_elevenlabs = False
                logger.warning("TTS: elevenlabs package not installed, using gTTS")
        else:
            self.use_elevenlabs = False
            logger.info("TTS: Using gTTS (no ElevenLabs key)")

    async def synthesize(self, text: str, speed: float = 1.0,
                          language: str = "en") -> Optional[str]:
        """
        Convert text to speech.
        Returns relative URL path to the audio file, or None on failure.
        """
        if not text or not text.strip():
            return None

        filename = f"{uuid.uuid4().hex[:12]}.mp3"
        filepath = OUTPUT_DIR / filename

        try:
            if self.use_elevenlabs:
                success = await self._synthesize_elevenlabs(text, filepath)
            else:
                success = await self._synthesize_gtts(text, filepath, speed, language)

            if success and filepath.exists():
                return f"/docs-output/audio/{filename}"
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")

        return None

    async def _synthesize_elevenlabs(self, text: str, filepath: Path) -> bool:
        """Generate audio via ElevenLabs API."""
        try:
            loop = asyncio.get_event_loop()

            def _generate():
                audio = self.el_client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=text,
                    model_id="eleven_turbo_v2",
                    output_format="mp3_22050_32",
                )
                with open(filepath, "wb") as f:
                    for chunk in audio:
                        f.write(chunk)
                return True

            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            return False

    async def _synthesize_gtts(self, text: str, filepath: Path,
                                speed: float = 1.0, language: str = "en") -> bool:
        """Generate audio via Google TTS (gTTS)."""
        try:
            from gtts import gTTS
            loop = asyncio.get_event_loop()

            def _generate():
                slow = speed < 0.8
                tts = gTTS(text=text, lang=language, slow=slow)
                tts.save(str(filepath))
                return True

            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
