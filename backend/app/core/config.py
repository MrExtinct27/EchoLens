from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"

import logging
logger = logging.getLogger(__name__)
if ENV_FILE.exists():
    logger.info(f"Loading .env file from: {ENV_FILE.absolute()}")
else:
    logger.warning(f".env file not found at: {ENV_FILE.absolute()}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE.absolute()),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    def __init__(self, **kwargs):
        # Explicitly load .env file values first to ensure they're read
        # This prevents issues where .env file might not be loaded properly
        if ENV_FILE.exists():
            try:
                env_values = dotenv_values(ENV_FILE)
                logger.info(f"Loaded {len(env_values)} values from .env file")
                
                # For S3 config, we want .env file to take precedence over system env vars
                # because system env vars might have old MinIO values
                s3_keys = ['S3_ENDPOINT', 'S3_BUCKET', 'S3_REGION', 'S3_ACCESS_KEY', 'S3_SECRET_KEY']
                
                # Pre-populate kwargs with .env values
                for key, value in env_values.items():
                    if key not in kwargs:
                        # For S3 keys, prefer .env file over system env vars (to avoid MinIO conflicts)
                        if key in s3_keys:
                            if key in os.environ:
                                logger.warning(f"⚠ System environment variable {key} is set but will be overridden by .env file")
                                logger.warning(f"   System env: {os.environ.get(key, '')[:20]}...")
                                logger.warning(f"   .env file: {value[:20] if value else 'empty'}...")
                            kwargs[key] = value
                        else:
                            # For other keys, system env vars take precedence (standard behavior)
                            if key not in os.environ:
                                kwargs[key] = value
                            else:
                                logger.debug(f"Environment variable {key} overrides .env file value")
            except Exception as e:
                logger.error(f"Error loading .env file: {e}")
        super().__init__(**kwargs)

    # Database
    DATABASE_URL: str = "postgresql+psycopg://app:app@localhost:5432/auditor"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # S3 Configuration (REQUIRED - no defaults to prevent MinIO fallback)
    # For AWS S3: Leave S3_ENDPOINT empty or set to your region endpoint (e.g., https://s3.us-east-1.amazonaws.com)
    # For AWS S3: S3_ACCESS_KEY and S3_SECRET_KEY are your AWS IAM credentials
    # For AWS S3: S3_BUCKET is your AWS S3 bucket name
    S3_ENDPOINT: str = ""  # Empty = use AWS S3 default endpoints
    S3_ACCESS_KEY: str = ""  # REQUIRED: AWS Access Key ID
    S3_SECRET_KEY: str = ""  # REQUIRED: AWS Secret Access Key
    S3_BUCKET: str = ""  # REQUIRED: AWS S3 bucket name
    S3_REGION: str = "us-east-1"  # AWS region where bucket is located
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_TRANSCRIBE_MODEL: str = "whisper-1"
    
    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # Processing providers
    TRANSCRIBE_PROVIDER: str = "openai"
    LLM_PROVIDER: str = "groq"
    
    # API
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://frontend:5173"]


settings = Settings()

# Debug: Log what values were loaded (after Settings initialization)
logger.info("=" * 60)
logger.info("S3 Configuration loaded from settings:")
logger.info(f"  S3_ENDPOINT: '{settings.S3_ENDPOINT}'")
logger.info(f"  S3_BUCKET: '{settings.S3_BUCKET}'")
logger.info(f"  S3_REGION: '{settings.S3_REGION}'")
logger.info(f"  S3_ACCESS_KEY: '{settings.S3_ACCESS_KEY[:8] if settings.S3_ACCESS_KEY else 'NOT SET'}...' (masked)")
logger.info(f"  .env file path: {ENV_FILE.absolute()}")
logger.info(f"  .env file exists: {ENV_FILE.exists()}")
# Check if there are system environment variables that might override
import os
sys_s3_endpoint = os.environ.get('S3_ENDPOINT', None)
if sys_s3_endpoint:
    logger.warning(f"⚠ WARNING: S3_ENDPOINT environment variable found: '{sys_s3_endpoint}'")
    logger.warning(f"  This may override .env file value. To use .env, unset this env var or remove it from your shell config.")
logger.info("=" * 60)

