import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import routes_upload, routes_calls, routes_metrics, routes_analytics, routes_s3_import

# Import storage_service with error handling
try:
    from app.services.storage import storage_service
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize storage service: {e}", exc_info=True)
    storage_service = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Customer Support Auditor API",
    description="Multi-modal customer support call analysis system with OpenAI & Groq",
    version="2.0.0"
)

cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins + settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

app.include_router(routes_upload.router)
app.include_router(routes_calls.router)
app.include_router(routes_metrics.router)
app.include_router(routes_analytics.router)
app.include_router(routes_s3_import.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Customer Support Auditor API...")
    
    openai_key = (settings.OPENAI_API_KEY or "").strip()
    groq_key = (settings.GROQ_API_KEY or "").strip()
    
    has_openai_key = openai_key and len(openai_key) > 20 and (openai_key.startswith("sk-") or openai_key.startswith("sk-proj-"))
    has_groq_key = groq_key and len(groq_key) > 10 and groq_key.startswith("gsk_")
    
    logger.info(f"Transcription provider: {settings.TRANSCRIBE_PROVIDER}")
    if has_openai_key:
        logger.info(f"✓ OpenAI API key found (length: {len(openai_key)})")
        logger.info(f"✓ Will use OpenAI model: {settings.OPENAI_TRANSCRIBE_MODEL}")
    else:
        logger.warning("⚠ OPENAI_API_KEY is missing or invalid. Transcription will fail until key is configured.")
    
    logger.info(f"Analysis provider: {settings.LLM_PROVIDER}")
    if has_groq_key:
        logger.info(f"✓ Groq API key found (length: {len(groq_key)})")
        logger.info(f"✓ Will use Groq model: {settings.GROQ_MODEL}")
    else:
        logger.warning("⚠ GROQ_API_KEY is missing or invalid. Analysis will fail until key is configured.")
    
    # Verify S3 configuration (non-blocking - app will start even if check fails)
    if storage_service is None:
        logger.error("⚠ Storage service not initialized. S3 operations will fail.")
        logger.error("   Fix the S3 configuration in your .env file to resolve issues.")
    else:
        logger.info("Verifying S3 configuration...")
        bucket_accessible = storage_service.ensure_bucket()
        if bucket_accessible:
            logger.info("✓ S3 bucket initialized and accessible")
        else:
            logger.warning("⚠ S3 bucket verification failed (see warnings above)")
            logger.warning("   The app will continue, but S3 operations may fail.")
            logger.warning("   Fix the S3 configuration in your .env file to resolve issues.")


@app.get("/")
def root():
    try:
        return {
            "message": "Customer Support Auditor API",
            "docs": "/docs",
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}", exc_info=True)
        return {
            "message": "Customer Support Auditor API",
            "docs": "/docs",
            "status": "error",
            "error": str(e)
        }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/debug/config")
def debug_config():
    """Debug endpoint to see what configuration values are being loaded."""
    import os
    from app.core.config import ENV_FILE
    
    try:
        storage_bucket = storage_service.bucket if hasattr(storage_service, 'bucket') else "NOT INITIALIZED"
        storage_region = storage_service.s3_client.meta.region_name if hasattr(storage_service, 's3_client') else "NOT INITIALIZED"
    except Exception as e:
        storage_bucket = f"ERROR: {str(e)}"
        storage_region = f"ERROR: {str(e)}"
    
    return {
        "env_file_path": str(ENV_FILE.absolute()),
        "env_file_exists": ENV_FILE.exists(),
        "settings_values": {
            "S3_ENDPOINT": settings.S3_ENDPOINT,
            "S3_BUCKET": settings.S3_BUCKET,
            "S3_REGION": settings.S3_REGION,
            "S3_ACCESS_KEY": settings.S3_ACCESS_KEY[:10] + "..." if settings.S3_ACCESS_KEY else "NOT SET",
            "S3_ACCESS_KEY_LENGTH": len(settings.S3_ACCESS_KEY) if settings.S3_ACCESS_KEY else 0,
            "S3_ACCESS_KEY_PREFIX": settings.S3_ACCESS_KEY[:4] if settings.S3_ACCESS_KEY else "N/A",
            "S3_SECRET_KEY": "***MASKED***" if settings.S3_SECRET_KEY else "NOT SET",
            "S3_SECRET_KEY_LENGTH": len(settings.S3_SECRET_KEY) if settings.S3_SECRET_KEY else 0,
        },
        "storage_service": {
            "bucket": storage_bucket,
            "region": storage_region,
        },
        "environment_variables": {
            "S3_ENDPOINT": os.environ.get("S3_ENDPOINT", "NOT SET"),
            "S3_BUCKET": os.environ.get("S3_BUCKET", "NOT SET"),
            "S3_REGION": os.environ.get("S3_REGION", "NOT SET"),
            "AWS_ACCESS_KEY_ID": "SET" if os.environ.get("AWS_ACCESS_KEY_ID") else "NOT SET",
            "AWS_SECRET_ACCESS_KEY": "SET" if os.environ.get("AWS_SECRET_ACCESS_KEY") else "NOT SET",
        },
        "note": "If environment variables are set, they override .env file values. Unset them to use .env file."
    }

