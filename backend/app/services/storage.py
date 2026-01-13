import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.core.config import settings
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        # Log what we're reading from settings (for debugging)
        logger.info("Reading S3 configuration from settings...")
        logger.info(f"  S3_ENDPOINT (raw): '{settings.S3_ENDPOINT}'")
        logger.info(f"  S3_BUCKET (raw): '{settings.S3_BUCKET}'")
        logger.info(f"  S3_REGION (raw): '{settings.S3_REGION}'")
        logger.info(f"  S3_ACCESS_KEY (raw): '{settings.S3_ACCESS_KEY[:8] if settings.S3_ACCESS_KEY else None}...' (masked)")
        
        # Validate required S3 configuration
        if not settings.S3_ACCESS_KEY or not settings.S3_ACCESS_KEY.strip():
            raise ValueError("S3_ACCESS_KEY is required in .env file. Please configure your AWS credentials.")
        
        if not settings.S3_SECRET_KEY or not settings.S3_SECRET_KEY.strip():
            raise ValueError("S3_SECRET_KEY is required in .env file. Please configure your AWS credentials.")
        
        if not settings.S3_BUCKET or not settings.S3_BUCKET.strip():
            raise ValueError("S3_BUCKET is required in .env file. Please specify your AWS S3 bucket name.")
        
        # Normalize endpoint URL
        endpoint_url = None
        raw_endpoint = settings.S3_ENDPOINT.strip() if settings.S3_ENDPOINT else ""
        
        logger.info(f"  Processed S3_ENDPOINT from settings: '{raw_endpoint}'")
        
        # If we detect MinIO endpoint, try reading directly from .env file as a fallback
        if raw_endpoint.startswith("http://localhost:9000") or raw_endpoint.startswith("http://127.0.0.1:9000"):
            logger.warning(f"⚠ MinIO endpoint detected in settings: '{raw_endpoint}'")
            logger.warning(f"  Attempting to read .env file directly as fallback...")
            
            # Try reading .env file directly
            from app.core.config import ENV_FILE
            if ENV_FILE.exists():
                from dotenv import dotenv_values
                try:
                    env_values = dotenv_values(ENV_FILE)
                    direct_endpoint = env_values.get('S3_ENDPOINT', '').strip()
                    logger.info(f"  S3_ENDPOINT from .env file (direct read): '{direct_endpoint}'")
                    
                    if direct_endpoint and not (direct_endpoint.startswith("http://localhost:9000") or direct_endpoint.startswith("http://127.0.0.1:9000")):
                        logger.info(f"  ✓ Using endpoint from .env file directly: '{direct_endpoint}'")
                        raw_endpoint = direct_endpoint
                    else:
                        raise ValueError(
                            f"MinIO endpoint detected in .env file ({direct_endpoint}). "
                            f"This application uses AWS S3. Please update your .env file with: "
                            f"S3_ENDPOINT=https://s3.us-east-2.amazonaws.com (or leave empty for AWS defaults)"
                        )
                except Exception as e:
                    logger.error(f"  Failed to read .env file directly: {e}")
                    raise ValueError(
                        f"MinIO endpoint detected ({raw_endpoint}). This application uses AWS S3. "
                        f"Please check your .env file and ensure S3_ENDPOINT is either empty or set to your AWS region endpoint "
                        f"(e.g., https://s3.us-east-2.amazonaws.com). "
                        f"Current value from config: '{raw_endpoint}'"
                    )
            else:
                raise ValueError(
                    f"MinIO endpoint detected ({raw_endpoint}). This application uses AWS S3. "
                    f"Please check your .env file and ensure S3_ENDPOINT is either empty or set to your AWS region endpoint "
                    f"(e.g., https://s3.us-east-2.amazonaws.com). "
                    f"Current value from config: '{raw_endpoint}'"
                )
        
        if raw_endpoint:
            endpoint_url = raw_endpoint
        
        # Extract region from endpoint if provided, otherwise use S3_REGION setting
        region = settings.S3_REGION.strip() if settings.S3_REGION else "us-east-1"
        
        # If endpoint URL is provided, try to extract region from it
        if endpoint_url and 'us-east-' in endpoint_url:
            # Extract region from endpoint like https://s3.us-east-2.amazonaws.com
            import re
            match = re.search(r's3\.([a-z0-9-]+)\.amazonaws\.com', endpoint_url)
            if match:
                extracted_region = match.group(1)
                logger.info(f"Extracted region '{extracted_region}' from endpoint URL")
                region = extracted_region
        
        client_kwargs = {
            "aws_access_key_id": settings.S3_ACCESS_KEY.strip(),
            "aws_secret_access_key": settings.S3_SECRET_KEY.strip(),
            "config": Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
            "region_name": region,
        }
        
        # Only add endpoint_url if explicitly provided (for custom AWS endpoints)
        # If empty/None, boto3 will use AWS default endpoints
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
            logger.info(f"Using custom S3 endpoint: {endpoint_url}")
        else:
            logger.info(f"Using AWS S3 default endpoints for region: {region}")
        
        logger.info(f"Configured S3 region: {region} (from S3_REGION setting: {settings.S3_REGION})")
        
        # Create boto3 client - use thread-local session for safety in multiprocessing
        self._boto3_session = None
        self.s3_client = boto3.client("s3", **client_kwargs)
        self.bucket = settings.S3_BUCKET.strip()  # Remove any trailing spaces
        
        # Disable SSL verification warnings in multiprocessing (can cause issues)
        import warnings
        warnings.filterwarnings('ignore', category=ResourceWarning)
        
        # Log configuration (without exposing secrets)
        logger.info(f"S3 Configuration:")
        logger.info(f"  Bucket: {self.bucket}")
        logger.info(f"  Region: {region}")
        logger.info(f"  Endpoint: {endpoint_url or 'AWS Default'}")
        logger.info(f"  Access Key: {settings.S3_ACCESS_KEY[:8] if len(settings.S3_ACCESS_KEY) > 8 else settings.S3_ACCESS_KEY}... (masked)")
        logger.info(f"  Secret Key: {'*' * 20} (masked)")
        logger.info(f"  Access Key length: {len(settings.S3_ACCESS_KEY) if settings.S3_ACCESS_KEY else 0} chars")
        logger.info(f"  Secret Key length: {len(settings.S3_SECRET_KEY) if settings.S3_SECRET_KEY else 0} chars")
        
        # Verify bucket name from settings
        if self.bucket == "calls" or not self.bucket:
            logger.error(f"❌ ERROR: Bucket name is '{self.bucket}' (old default or empty)")
            logger.error(f"   Expected bucket: 'echolens-call-recordings'")
            logger.error(f"   This suggests .env file is not being loaded correctly.")
            
            # Try to read bucket directly from .env file
            from app.core.config import ENV_FILE
            if ENV_FILE.exists():
                from dotenv import dotenv_values
                try:
                    env_values = dotenv_values(ENV_FILE)
                    direct_bucket = env_values.get('S3_BUCKET', '').strip()
                    if direct_bucket and direct_bucket != self.bucket:
                        logger.warning(f"   Found S3_BUCKET='{direct_bucket}' in .env file directly")
                        logger.warning(f"   Using bucket from .env file: {direct_bucket}")
                        self.bucket = direct_bucket
                except Exception as e:
                    logger.error(f"   Failed to read .env file directly: {e}")
            
            if self.bucket == "calls" or not self.bucket:
                raise ValueError(
                    f"S3_BUCKET is '{self.bucket}' (old default). "
                    f"Please set S3_BUCKET=echolens-call-recordings in your .env file and restart."
                )

    def ensure_bucket(self):
        """
        Verify bucket exists and is accessible. 
        This is a best-effort check - if it fails, we log warnings but don't fail startup.
        Actual operations will show clearer errors if there are permission issues.
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"✓ S3 bucket verified: {self.bucket}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            status_code = e.response.get('ResponseMetadata', {}).get('HTTPStatusCode', '')
            
            if status_code == 301:
                # 301 Moved Permanently means bucket exists but in different region
                error_msg = str(e)
                logger.error(f"❌ S3 bucket '{self.bucket}' exists but is in a different region.")
                logger.error(f"   Error: {error_msg}")
                logger.error(f"   Current configured region: {self.s3_client.meta.region_name}")
                logger.error(f"   Please update S3_REGION in your .env file to match the bucket's actual region.")
                logger.error(f"   Or update S3_ENDPOINT to point to the correct region (e.g., https://s3.BUCKET-REGION.amazonaws.com)")
                logger.warning(f"   Continuing anyway - bucket operations may fail. Fix the region to resolve this.")
                return False
            elif error_code == '404':
                logger.warning(f"⚠ S3 bucket '{self.bucket}' not found. Please create it in AWS S3 console or ensure bucket name is correct.")
                logger.warning(f"   Continuing anyway - bucket operations will fail until bucket exists.")
                return False
            elif error_code == '403':
                current_region = self.s3_client.meta.region_name if hasattr(self, 's3_client') else 'unknown'
                logger.warning(f"⚠ Access denied (403) to S3 bucket '{self.bucket}'.")
                logger.warning(f"   Possible causes:")
                logger.warning(f"   1. IAM credentials don't match the IAM user with S3 permissions")
                logger.warning(f"   2. Bucket policy is blocking access (check bucket permissions in AWS console)")
                logger.warning(f"   3. IAM policy hasn't propagated yet (wait 1-2 minutes and try again)")
                logger.warning(f"   4. Wrong AWS account (credentials might be from different account)")
                logger.warning(f"   5. Region mismatch (bucket might be in different region)")
                logger.warning(f"   Troubleshooting steps:")
                logger.warning(f"     - Verify S3_ACCESS_KEY and S3_SECRET_KEY in .env match the IAM user")
                logger.warning(f"     - Check bucket policy in AWS S3 console (doesn't deny your IAM user)")
                logger.warning(f"     - Verify bucket region matches S3_REGION in .env (current: {current_region})")
                logger.warning(f"     - Try: aws s3 ls s3://{self.bucket} --region {current_region} (to test credentials)")
                logger.warning(f"   Continuing anyway - bucket operations will fail with clearer errors.")
                return False
            else:
                logger.warning(f"⚠ Error checking S3 bucket '{self.bucket}': {str(e)}")
                logger.warning(f"   Error code: {error_code}, Status: {status_code}")
                logger.warning(f"   Continuing anyway - bucket operations will show clearer errors.")
                return False

    def presign_put(self, object_key: str, content_type: str = "audio/wav", expires: int = 3600) -> str:
        """Generate a presigned PUT URL for uploading."""
        url = self.s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires,
        )
        return url

    def download_object(self, object_key: str) -> str:
        """Download object to a temporary file and return the path. Preserves the original file extension."""
        try:
            _, ext = os.path.splitext(object_key)
            if not ext:
                ext = ".wav"
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            try:
                # Use download_fileobj with error handling for SIGSEGV prevention
                self.s3_client.download_fileobj(self.bucket, object_key, temp_file)
                temp_file.flush()  # Ensure all data is written
                os.fsync(temp_file.fileno())  # Force write to disk
            finally:
                temp_file.close()
            
            return temp_file.name
        except Exception as e:
            logger.error(f"Error downloading {object_key}: {e}", exc_info=True)
            raise

    def object_exists(self, object_key: str) -> bool:
        """Check if object exists."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError:
            return False

    def list_all_objects(self, prefix: str = "") -> list[dict]:
        """
        List ALL objects in S3 bucket with given prefix (for debugging).
        Returns list of all objects regardless of extension.
        """
        all_objects = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        # Skip directory markers
                        if key.endswith('/'):
                            continue
                        all_objects.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat() if 'LastModified' in obj else None
                        })
            
            return sorted(all_objects, key=lambda x: x['key'])
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDenied':
                raise Exception(f"Access denied to S3 bucket. Check your AWS credentials and IAM permissions.")
            elif error_code == 'NoSuchBucket':
                raise Exception(f"S3 bucket '{self.bucket}' does not exist. Please create it in AWS S3 console.")
            else:
                raise Exception(f"Error listing S3 objects: {str(e)}")

    def list_objects(self, prefix: str = "") -> list[dict]:
        """
        List all objects in S3 bucket with given prefix. Returns list of objects with key, size, and last_modified.
        Only returns audio files (filters by extension).
        """
        audio_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.webm', '.flac', '.mp4', '.aac', '.wma', '.opus', '.mpeg', '.mpga', '.wmv'}
        objects = []
        
        try:
            logger.info(f"Listing objects in bucket '{self.bucket}' with prefix '{prefix}'")
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            
            total_scanned = 0
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_scanned += 1
                        key = obj['Key']
                        # Skip if it's a directory marker (ends with /)
                        if key.endswith('/'):
                            logger.debug(f"Skipping directory marker: {key}")
                            continue
                        # Only include audio files
                        _, ext = os.path.splitext(key.lower())
                        if ext in audio_extensions:
                            objects.append({
                                'key': key,
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'].isoformat() if 'LastModified' in obj else None
                            })
                            logger.debug(f"Found audio file: {key} (ext: {ext})")
                        else:
                            logger.debug(f"Skipping non-audio file: {key} (ext: {ext})")
            
            logger.info(f"Scanned {total_scanned} objects, found {len(objects)} audio files")
            
            if total_scanned > 0 and len(objects) == 0:
                # Try to list a few sample files to help debug
                sample_objects = self.list_all_objects(prefix)
                if sample_objects:
                    logger.warning(f"Found {len(sample_objects)} objects but none matched audio extensions. Sample: {[o['key'] for o in sample_objects[:3]]}")
            
            return sorted(objects, key=lambda x: x['key'])
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDenied':
                raise Exception(f"Access denied to S3 bucket. Check your AWS credentials and IAM permissions.")
            elif error_code == 'NoSuchBucket':
                raise Exception(f"S3 bucket '{self.bucket}' does not exist. Please create it in AWS S3 console.")
            else:
                raise Exception(f"Error listing S3 objects: {str(e)}")


storage_service = StorageService()

