"""
Voice memos: a short recording in, plain text out.

One call to OpenAI's audio transcription API (model `gpt-4o-transcribe` by
default, about $0.006 per audio minute). It handles English, Spanish,
Vietnamese, Chinese and many more in the same call, so the vendor never picks a
language. The recording itself is not stored: it is sent, transcribed, and
dropped. The text goes back to the vendor to check and fix before anything is
sent to the interviewer, because transcription can slip, especially in a noisy
market and in less common languages.

Turned on by setting OPENAI_API_KEY. Without it, `available()` is False and the
app hides the record button. With BB_FAKE_LLM=1 it returns a fixed sentence.
"""

from __future__ import annotations

import logging
import os

import httpx

from core.config import FAKE_LLM

logger = logging.getLogger(__name__)

STT_URL = "https://api.openai.com/v1/audio/transcriptions"
STT_MODEL = os.getenv("BB_STT_MODEL", "gpt-4o-transcribe")
MAX_AUDIO_BYTES = 12 * 1024 * 1024      # about 10+ minutes of compressed speech; OpenAI allows 25 MB
MIN_AUDIO_BYTES = 2000                  # anything smaller is a mis-tap
FAKE_TRANSCRIPT = "Sold nine of twelve moon pendants before noon at the north arcade."

_EXT = {"webm": "webm", "ogg": "ogg", "mp4": "m4a", "m4a": "m4a", "mpeg": "mp3", "mp3": "mp3", "wav": "wav", "x-wav": "wav",
        "aac": "m4a", "x-m4a": "m4a"}


class SpeechError(Exception):
    """Something to tell the vendor in plain words."""

    def __init__(self, message: str, status: int = 503):
        super().__init__(message)
        self.status = status


def available() -> bool:
    return FAKE_LLM or bool(os.getenv("OPENAI_API_KEY"))


def filename_for(content_type: str) -> str:
    sub = (content_type or "").split(";")[0].split("/")[-1].lower()
    return f"memo.{_EXT.get(sub, 'webm')}"


async def transcribe(data: bytes, content_type: str) -> str:
    """Return the words in the recording. Raises SpeechError with a message fit to show."""
    if FAKE_LLM:
        return FAKE_TRANSCRIPT
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SpeechError("Voice isn't switched on yet. Please type for now.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
            r = await client.post(
                STT_URL, headers={"Authorization": f"Bearer {key}"},
                files={"file": (filename_for(content_type), data, (content_type or "audio/webm").split(";")[0])},
                data={"model": STT_MODEL, "response_format": "json"},
            )
    except httpx.HTTPError as e:
        logger.error(f"[Speech] request failed: {type(e).__name__}")
        raise SpeechError("We couldn't reach the transcription service. Please try again, or type it.") from e
    if r.status_code != 200:
        logger.error(f"[Speech] {r.status_code}: {r.text[:300]}")
        raise SpeechError("We couldn't turn that into text just now. Please try again, or type it.")
    text = (r.json().get("text") or "").strip()
    if not text:
        raise SpeechError("We didn't hear anything in that recording. Please try again a little closer to the phone.", 422)
    return text
