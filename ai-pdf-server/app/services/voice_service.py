"""Voice service for Speech-to-Text and Text-to-Speech using OpenAI."""

import asyncio
import base64
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)

# Thread pool for audio processing
_executor = ThreadPoolExecutor(max_workers=4)


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""

    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class SpeechResult:
    """Result from text-to-speech synthesis."""

    audio_data: bytes
    format: str = "mp3"
    voice: str = "alloy"


class VoiceService:
    """
    Service for voice processing using OpenAI Whisper and TTS.

    Provides:
    - Speech-to-Text (STT) using Whisper
    - Text-to-Speech (TTS) using OpenAI TTS
    - Audio streaming support
    """

    # Available TTS voices with characteristics
    VOICES = {
        "alloy": "Neutral, balanced voice",
        "echo": "Warm, engaging voice",
        "fable": "Expressive, animated voice",
        "onyx": "Deep, authoritative voice",
        "nova": "Friendly, conversational voice - great for teaching",
        "shimmer": "Clear, pleasant voice",
    }

    # Teacher voice (friendly and engaging)
    DEFAULT_TEACHER_VOICE = "nova"

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_voice: Optional[str] = None,
    ):
        """
        Initialize voice service.

        Args:
            api_key: OpenAI API key
            default_voice: Default TTS voice
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.default_voice = default_voice or self.DEFAULT_TEACHER_VOICE

        if not self.api_key:
            logger.warning("OpenAI API key not configured for voice service")

        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text using OpenAI Whisper.

        Args:
            audio_data: Audio file bytes (mp3, wav, webm, etc.)
            language: Optional language code (e.g., 'en', 'es')
            prompt: Optional prompt to guide transcription

        Returns:
            TranscriptionResult with transcribed text
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        logger.info("Starting audio transcription", audio_size=len(audio_data))

        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                # Open and transcribe
                with open(tmp_path, "rb") as audio_file:
                    kwargs = {"model": "whisper-1", "file": audio_file}

                    if language:
                        kwargs["language"] = language
                    if prompt:
                        kwargs["prompt"] = prompt

                    response = await self.client.audio.transcriptions.create(**kwargs)

                logger.info(
                    "Transcription complete",
                    text_length=len(response.text),
                )

                return TranscriptionResult(
                    text=response.text,
                    language=language,
                )

            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            raise

    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> SpeechResult:
        """
        Convert text to speech using OpenAI TTS.

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            response_format: Audio format (mp3, opus, aac, flac)

        Returns:
            SpeechResult with audio data
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        voice = voice or self.default_voice
        speed = max(0.25, min(4.0, speed))

        logger.info(
            "Synthesizing speech",
            text_length=len(text),
            voice=voice,
            speed=speed,
        )

        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed,
                response_format=response_format,
            )

            # Get audio bytes
            audio_data = response.content

            logger.info(
                "Speech synthesis complete",
                audio_size=len(audio_data),
                format=response_format,
            )

            return SpeechResult(
                audio_data=audio_data,
                format=response_format,
                voice=voice,
            )

        except Exception as e:
            logger.error("Speech synthesis failed", error=str(e))
            raise

    async def synthesize_speech_hd(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        response_format: str = "mp3",
    ) -> SpeechResult:
        """
        Convert text to high-quality speech using OpenAI TTS-HD.

        Args:
            text: Text to convert to speech
            voice: Voice to use
            speed: Speech speed
            response_format: Audio format

        Returns:
            SpeechResult with HD audio data
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        voice = voice or self.default_voice

        try:
            response = await self.client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text,
                speed=speed,
                response_format=response_format,
            )

            return SpeechResult(
                audio_data=response.content,
                format=response_format,
                voice=voice,
            )

        except Exception as e:
            logger.error("HD speech synthesis failed", error=str(e))
            raise

    async def stream_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream speech synthesis for real-time playback.

        Args:
            text: Text to convert
            voice: Voice to use
            speed: Speech speed

        Yields:
            Audio chunks as bytes
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")

        voice = voice or self.default_voice

        try:
            async with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed,
                response_format="mp3",
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk

        except Exception as e:
            logger.error("Speech streaming failed", error=str(e))
            raise

    def audio_to_base64(self, audio_data: bytes) -> str:
        """Convert audio bytes to base64 string."""
        return base64.b64encode(audio_data).decode("utf-8")

    def base64_to_audio(self, base64_string: str) -> bytes:
        """Convert base64 string to audio bytes."""
        return base64.b64decode(base64_string)

    async def health_check(self) -> bool:
        """Check if voice service is healthy."""
        if not self.client:
            return False

        try:
            # Quick TTS test
            result = await self.synthesize_speech("Test", speed=2.0)
            return len(result.audio_data) > 0
        except Exception:
            return False

    def get_available_voices(self) -> dict:
        """Get list of available TTS voices."""
        return self.VOICES.copy()


# Singleton instance
voice_service = VoiceService()
