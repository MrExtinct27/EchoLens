import json
import re
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError
from groq import Groq
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalysisOutput(BaseModel):
    customer_sentiment: str = Field(..., pattern=r"^(positive|neutral|negative)$")
    topic: str = Field(..., pattern=r"^(billing_issue|tech_support|cancellation|shipping|other)$")
    problem_resolved: bool
    summary: str = Field(..., max_length=240)
    confidence: float = Field(..., ge=0.0, le=1.0)


class AnalyzeService:
    def __init__(self):
        api_key = (settings.GROQ_API_KEY or "").strip()
        is_valid_key = api_key and len(api_key) > 10 and api_key.startswith("gsk_")

        if settings.LLM_PROVIDER == "groq" and is_valid_key:
            self.provider = "groq"
            self._groq_client = Groq(api_key=api_key)
            logger.info("AnalyzeService initialized with Groq provider")
        else:
            raise ValueError(
                f"Groq analysis requires LLM_PROVIDER=groq and valid GROQ_API_KEY. "
                f"Provider: {settings.LLM_PROVIDER}, Key present: {bool(api_key)}"
            )

    def analyze(self, transcript: str) -> Dict[str, Any]:
        """Analyze transcript and return structured insights."""
        return self._groq_analyze(transcript)

    def _groq_analyze(self, transcript: str) -> Dict[str, Any]:
        """Analyze transcript using Groq LLM with JSON-only output and retry logic."""
        logger.info(f"Analyzing transcript using Groq model: {settings.GROQ_MODEL}")

        system_prompt = """You are a customer support call analyst. Extract structured data from the transcript.

You MUST respond with ONLY valid JSON, no markdown, no prose, no explanations.
The JSON must match this exact schema:
{
  "customer_sentiment": "positive" | "neutral" | "negative",
  "topic": "billing_issue" | "tech_support" | "cancellation" | "shipping" | "other",
  "problem_resolved": true | false,
  "summary": "brief summary (max 240 chars)",
  "confidence": 0.0-1.0
}

Rules:
- sentiment: overall customer emotion (positive/neutral/negative)
- topic: primary issue category
- problem_resolved: was the customer's problem solved in this call?
- summary: concise summary (maximum 240 characters)
- confidence: your confidence in this analysis (0.0 to 1.0)

Return ONLY the JSON object, nothing else."""

        user_prompt = f"""Analyze this customer support call transcript:

{transcript}

Return ONLY valid JSON matching the schema."""

        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Groq API call attempt {attempt + 1}/{max_retries + 1}")

                response = self._groq_client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_completion_tokens=500,
                    response_format={"type": "json_object"}
                )

                response_text = response.choices[0].message.content.strip()
                json_text = self._extract_json(response_text)
                data = json.loads(json_text)
                validated = AnalysisOutput(**data)
                result = validated.model_dump()

                logger.info(f"Analysis successful. Sentiment: {result['customer_sentiment']}, Topic: {result['topic']}, Confidence: {result['confidence']}")
                return result

            except json.JSONDecodeError as e:
                if attempt < max_retries:
                    logger.warning(f"JSON decode error, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    continue
                raise ValueError(f"Failed to parse JSON response after {max_retries + 1} attempts: {e}")

            except ValidationError as e:
                if attempt < max_retries:
                    logger.warning(f"Validation error, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    continue
                raise ValueError(f"Failed to validate analysis output after {max_retries + 1} attempts: {e}")

            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Groq API error, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                    continue
                logger.error(f"Groq API failed after {max_retries + 1} attempts")
                raise

        raise RuntimeError("Unexpected: all retries exhausted but no exception raised")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)

        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)

        return text.strip()


try:
    analyze_service = AnalyzeService()
    logger.info(f"AnalyzeService initialized with provider: {analyze_service.provider}")
except ValueError as e:
    logger.error(f"AnalyzeService initialization failed: {e}")
    analyze_service = None
