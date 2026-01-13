import os
import logging
from typing import Tuple
import requests
from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscribeService:
    def __init__(self):
        api_key = (settings.OPENAI_API_KEY or "").strip()
        is_valid_key = api_key and len(api_key) > 20 and (api_key.startswith("sk-") or api_key.startswith("sk-proj-"))
        
        if settings.TRANSCRIBE_PROVIDER == "openai" and is_valid_key:
            self.provider = "openai"
            logger.info("TranscribeService initialized with OpenAI provider")
        else:
            raise ValueError(
                f"OpenAI transcription requires TRANSCRIBE_PROVIDER=openai and valid OPENAI_API_KEY. "
                f"Provider: {settings.TRANSCRIBE_PROVIDER}, Key present: {bool(api_key)}"
            )

    def transcribe(self, audio_path: str) -> Tuple[str, str]:
        """Transcribe audio file to text with automatic fallback to whisper-1 on format errors."""
        preferred_model = settings.OPENAI_TRANSCRIBE_MODEL
        fallback_model = "whisper-1"

        if preferred_model == fallback_model:
            return self._openai_transcribe(audio_path, model=preferred_model)

        try:
            logger.info(f"Attempting transcription with preferred model: {preferred_model}")
            return self._openai_transcribe(audio_path, model=preferred_model)
        except Exception as e:
            error_msg = str(e).lower()
            error_text = str(e)

            is_format_error = (
                "unsupported_format" in error_msg
                or '"param": "messages"' in error_text
                or '"code": "unsupported_format"' in error_text
                or "this model does not support the format" in error_msg
            )

            if is_format_error:
                logger.warning(f"{preferred_model} failed with format error. Falling back to {fallback_model}.")
                return self._openai_transcribe(audio_path, model=fallback_model)
            else:
                raise

    def _openai_transcribe(self, audio_path: str, model: str = None) -> Tuple[str, str]:
        """Transcribe audio using OpenAI API via direct REST call."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        api_key = (settings.OPENAI_API_KEY or "").strip()
        if not api_key or len(api_key) < 20 or not (api_key.startswith("sk-") or api_key.startswith("sk-proj-")):
            raise ValueError("Valid OPENAI_API_KEY required for transcription")

        if model is None:
            model = settings.OPENAI_TRANSCRIBE_MODEL

        if model in ["gpt-4o-mini-transcribe", "gpt-4o-transcribe", "gpt-4o-transcribe-diarize"]:
            response_format = "json"
        else:
            response_format = "text"

        logger.info(f"Transcribing via OpenAI REST API: model={model}, response_format={response_format}")

        try:
            with open(audio_path, "rb") as f:
                file_content = f.read()

            file_size = len(file_content)
            if file_size < 1024:
                raise ValueError(f"File too small ({file_size} bytes). Likely invalid or partial download.")

            head = file_content[:32]
            if head.startswith(b'<?xml') or head.startswith(b'<!DOCTYPE') or head.startswith(b'<html'):
                raise ValueError(f"File appears to be HTML/XML, not audio. First bytes: {head[:50]!r}")
            if head.startswith(b'{') or head.startswith(b'['):
                raise ValueError(f"File appears to be JSON, not audio. First bytes: {head[:50]!r}")

            detected_format = self._detect_audio_format(file_content)
            file_ext = os.path.splitext(audio_path)[1].lower()

            format_to_content_type = {
                'wav': 'audio/wav',
                'mp3': 'audio/mpeg',
                'mp4': 'audio/mp4',
                'm4a': 'audio/m4a',
                'ogg': 'audio/ogg',
                'webm': 'audio/webm',
                'flac': 'audio/flac',
                'unknown': 'audio/mpeg'
            }

            if detected_format != "unknown":
                actual_format = detected_format
                content_type = format_to_content_type.get(detected_format, 'audio/mpeg')
                extension = f".{detected_format}"
            else:
                actual_format = file_ext.lstrip('.') if file_ext else "unknown"
                extension_map = {
                    '.wav': 'audio/wav',
                    '.mp3': 'audio/mpeg',
                    '.mp4': 'audio/mp4',
                    '.m4a': 'audio/m4a',
                    '.ogg': 'audio/ogg',
                    '.webm': 'audio/webm',
                    '.flac': 'audio/flac',
                    '.mpeg': 'audio/mpeg',
                    '.mpga': 'audio/mpeg'
                }
                content_type = extension_map.get(file_ext, 'audio/mpeg')
                extension = file_ext if file_ext else ".mp3"

            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            filename = f"{base_name}{extension}"

            logger.info(f"Format: {actual_format}, content_type: {content_type}, filename: {filename}")

            if detected_format == "unknown" and file_ext:
                logger.warning(f"Could not detect format from magic bytes, using extension: {file_ext}")
            elif detected_format != "unknown" and file_ext.lstrip('.') != detected_format:
                logger.warning(f"Extension mismatch: {file_ext} vs detected {detected_format}")

            files = {"file": (filename, file_content, content_type)}
            data = {"model": model, "response_format": response_format}
            headers = {"Authorization": f"Bearer {api_key}"}

            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=120
            )

            if response.status_code != 200:
                error_msg = f"OpenAI API returned {response.status_code}: {response.text}"
                logger.error(error_msg)
                logger.error(f"File: {filename}, content_type: {content_type}, size: {file_size} bytes")
                logger.error(f"Detected format: {actual_format}, extension: {file_ext}")
                if len(file_content) >= 16:
                    logger.error(f"File signature: {file_content[:16].hex()}")
                raise Exception(error_msg)

            if response_format == "text":
                transcript_text = response.text.strip()
            else:
                payload = response.json()
                transcript_text = (payload.get("text") or "").strip()

            if not transcript_text:
                raise ValueError(f"Empty transcription response. status={response.status_code}")

            logger.info(f"Transcription completed. chars={len(transcript_text)}")
            return transcript_text, model

        except requests.exceptions.RequestException as e:
            logger.exception(f"HTTP request to OpenAI API failed: {e}")
            raise
        except Exception:
            logger.exception("OpenAI transcription failed")
            raise

    def _detect_audio_format(self, file_bytes: bytes) -> str:
        """Detect audio file format from magic bytes."""
        if len(file_bytes) < 4:
            return "unknown"

        if file_bytes[:3] == b'ID3':
            return "mp3"
        if file_bytes[0] == 0xFF and (file_bytes[1] & 0xE0) == 0xE0:
            return "mp3"

        if file_bytes[:4] == b'RIFF' and len(file_bytes) > 8 and file_bytes[8:12] == b'WAVE':
            return "wav"

        if file_bytes[:4] == bytes([0x1A, 0x45, 0xDF, 0xA3]):
            return "webm"

        if file_bytes[:4] == b'OggS':
            return "ogg"

        if file_bytes[:4] == b'fLaC':
            return "flac"

        if len(file_bytes) > 12 and file_bytes[4:8] == b'ftyp':
            if b'M4A ' in file_bytes[8:16] or b'isom' in file_bytes[8:16] or b'mp41' in file_bytes[8:16]:
                return "m4a"
            if b'mp4' in file_bytes[8:16].lower():
                return "mp4"

        return "unknown"


try:
    transcribe_service = TranscribeService()
    logger.info(f"TranscribeService initialized with provider: {transcribe_service.provider}")
except ValueError as e:
    logger.error(f"TranscribeService initialization failed: {e}")
    transcribe_service = None
