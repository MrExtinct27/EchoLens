from celery import Celery
from celery.signals import worker_ready
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "auditor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.process_call"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Use threads pool instead of prefork to avoid boto3/SSL segmentation faults
    worker_pool="threads",  # or "solo" for single process (safer but slower)
    worker_concurrency=2,  # Number of threads (lower to avoid resource issues)
    worker_prefetch_multiplier=1,  # Lower prefetch to avoid memory issues
    task_acks_late=True,  # Acknowledge tasks after completion
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
)


@worker_ready.connect
def on_worker_ready(sender=None, **kwargs):
    """Log worker configuration when worker starts and re-queue pending/failed tasks."""
    logger.info("=" * 60)
    logger.info("Celery Worker Starting - Configuration Check")
    logger.info("=" * 60)
    
    try:
        import openai
        logger.info(f"OpenAI SDK version: {openai.__version__}")
    except Exception as e:
        logger.warning(f"Could not get OpenAI SDK version: {e}")
    
    try:
        from app.services.transcribe import transcribe_service
        logger.info(f"Transcription Provider: {transcribe_service.provider}")
        logger.info(f"✓ Will use OpenAI model: {settings.OPENAI_TRANSCRIBE_MODEL}")
    except ValueError as e:
        logger.error(f"TranscribeService initialization failed: {e}")

    try:
        from app.services.analyze import analyze_service
        logger.info(f"Analysis Provider: {analyze_service.provider}")
        logger.info(f"✓ Will use Groq model: {settings.GROQ_MODEL}")
    except ValueError as e:
        logger.error(f"AnalyzeService initialization failed: {e}")
    
    logger.info("=" * 60)
    logger.info("Checking for pending/failed calls to re-queue...")
    logger.info("=" * 60)
    
    # Re-queue any pending or stuck processing calls
    try:
        from app.db.session import SessionLocal
        from app.db.models import Call
        from app.tasks.process_call import process_call_task
        
        db = SessionLocal()
        try:
            # Find calls that need processing:
            # 1. PENDING - never processed
            # 2. PROCESSING - worker crashed while processing (stuck)
            pending_calls = db.query(Call).filter(
                Call.status.in_(["PENDING", "PROCESSING"])
            ).all()
            
            if pending_calls:
                logger.info(f"Found {len(pending_calls)} pending/stuck calls to re-queue")
                
                requeued = 0
                for call in pending_calls:
                    try:
                        # Reset PROCESSING calls back to PENDING (they were stuck due to crash)
                        if call.status == "PROCESSING":
                            logger.info(f"Resetting stuck call {call.id} from PROCESSING to PENDING")
                            call.status = "PENDING"
                            db.commit()
                        
                        # Re-queue the call for processing
                        logger.info(f"Re-queuing call {call.id} (status: {call.status}, key: {call.audio_object_key})")
                        process_call_task.delay(str(call.id))
                        requeued += 1
                    except Exception as e:
                        logger.error(f"Error re-queuing call {call.id}: {e}", exc_info=True)
                        db.rollback()
                
                logger.info(f"✓ Successfully re-queued {requeued}/{len(pending_calls)} calls")
            else:
                logger.info("✓ No pending calls found - database is clean")
                
        except Exception as e:
            logger.error(f"Error checking for pending calls: {e}", exc_info=True)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Could not check for pending calls (database might not be available): {e}")
    
    logger.info("=" * 60)
    logger.info("Worker ready to process tasks")
    logger.info("=" * 60)

