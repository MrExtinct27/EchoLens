import os
import logging
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models import Call, Transcript, Analysis
from app.services.storage import storage_service
from app.services.transcribe import transcribe_service
from app.services.analyze import analyze_service

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.process_call.process_call_task")
def process_call_task(call_id: str):
    """Process a call: transcribe audio and analyze transcript."""
    db: Session = SessionLocal()
    call = None
    audio_path = None
    
    try:
        logger.info(f"Processing call: {call_id}")
        
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            raise ValueError(f"Call {call_id} not found")
        
        logger.info(f"Stage 1: Marking call {call_id} as PROCESSING")
        call.status = "PROCESSING"
        db.commit()
        
        logger.info(f"Stage 2: Downloading audio from S3: {call.audio_object_key}")
        audio_path = storage_service.download_object(call.audio_object_key)
        logger.info(f"Audio downloaded to: {audio_path}")
        
        if not os.path.exists(audio_path):
            raise ValueError(f"Downloaded file does not exist: {audio_path}")
        
        file_size = os.path.getsize(audio_path)
        logger.info(f"Downloaded file size: {file_size} bytes")
        
        if file_size < 1024:
            raise ValueError(f"Downloaded file too small ({file_size} bytes). Likely not valid audio or partial download.")
        
        with open(audio_path, "rb") as f:
            first_bytes = f.read(32)
            if first_bytes.startswith(b'<?xml') or first_bytes.startswith(b'<!DOCTYPE') or first_bytes.startswith(b'<html'):
                raise ValueError(f"Downloaded file appears to be HTML/XML, not audio. First bytes: {first_bytes[:50]!r}")
            if first_bytes.startswith(b'{') or first_bytes.startswith(b'['):
                raise ValueError(f"Downloaded file appears to be JSON, not audio. First bytes: {first_bytes[:50]!r}")
    
        if transcribe_service is None:
            raise ValueError("TranscribeService not initialized. Check TRANSCRIBE_PROVIDER and OPENAI_API_KEY in .env")
        
        logger.info(f"Stage 3: Transcribing audio using {transcribe_service.provider}")
        transcript_text, model_name = transcribe_service.transcribe(audio_path)
        logger.info(f"Transcription completed. Model: {model_name}, Length: {len(transcript_text)} chars")
        
        if analyze_service is None:
            raise ValueError("AnalyzeService not initialized. Check LLM_PROVIDER and GROQ_API_KEY in .env")
        
        logger.info(f"Stage 4: Analyzing transcript using {analyze_service.provider}")
        analysis_result = analyze_service.analyze(transcript_text)
        logger.info(f"Analysis completed. Sentiment: {analysis_result['customer_sentiment']}, Topic: {analysis_result['topic']}")
        
        logger.info(f"Stage 5: Saving transcript to database")
        transcript = Transcript(
            call_id=call.id,
            text=transcript_text,
            model=model_name
        )
        db.merge(transcript)
        
        logger.info(f"Stage 6: Saving analysis to database")
        analysis = Analysis(
            call_id=call.id,
            sentiment=analysis_result["customer_sentiment"],
            topic=analysis_result["topic"],
            problem_resolved=analysis_result["problem_resolved"],
            summary=analysis_result["summary"],
            confidence=analysis_result.get("confidence")
        )
        db.merge(analysis)
        
        logger.info(f"Stage 7: Marking call {call_id} as DONE")
        call.status = "DONE"
        db.commit()
        
        logger.info(f"Call {call_id} processed successfully")
        return {"status": "success", "call_id": str(call.id)}
        
    except Exception as e:
        logger.error(f"Error processing call {call_id}: {str(e)}", exc_info=True)
        if call:
            call.status = "FAILED"
            db.commit()
            logger.error(f"Call {call_id} marked as FAILED")
        raise e
    
    finally:
        if audio_path and os.path.exists(audio_path):
            logger.debug(f"Cleaning up temp file: {audio_path}")
            os.remove(audio_path)
        db.close()

