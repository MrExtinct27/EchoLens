from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
from pathlib import Path
from app.db.session import get_db
from app.db.models import Call
from app.services.storage import storage_service
from app.tasks.process_call import process_call_task
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/s3-import", tags=["s3-import"])


class S3FileInfo(BaseModel):
    key: str
    size: int
    last_modified: Optional[str] = None


class ListS3FilesResponse(BaseModel):
    files: List[S3FileInfo]
    count: int
    prefix: str


class BatchImportRequest(BaseModel):
    s3_keys: List[str]


class BatchImportResponse(BaseModel):
    total_files: int
    queued: int
    skipped: int
    errors: List[str]


@router.get("/debug-list-all")
def debug_list_all(prefix: str = ""):
    """
    Debug endpoint: List ALL objects (not just audio) with given prefix.
    Useful for debugging when no audio files are found.
    """
    try:
        prefix = prefix.strip() if prefix else ""
        logger.info(f"Debug: Listing ALL objects with prefix: '{prefix}'")
        
        all_objects = storage_service.list_all_objects(prefix)
        
        return {
            "prefix": prefix,
            "bucket": storage_service.bucket,
            "total_objects": len(all_objects),
            "objects": all_objects[:20],  # Limit to first 20 for response size
            "sample_keys": [obj['key'] for obj in all_objects[:10]]
        }
    except Exception as e:
        logger.error(f"Debug list error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Debug list failed: {str(e)}")


@router.get("/list", response_model=ListS3FilesResponse)
def list_s3_files(prefix: str = "", db: Session = Depends(get_db)):
    """
    List all audio files in S3 bucket with the given prefix.
    Returns list of files that can be imported.
    """
    try:
        # Normalize prefix - remove leading/trailing whitespace, but keep as-is
        # S3 prefix matching works with or without trailing slash
        prefix = prefix.strip() if prefix else ""
        
        logger.info(f"Listing S3 files with prefix: '{prefix}' (bucket: {storage_service.bucket})")
        
        files_data = storage_service.list_objects(prefix)
        
        logger.info(f"Found {len(files_data)} audio files with prefix '{prefix}'")
        if len(files_data) > 0:
            logger.info(f"Sample files: {[f['key'] for f in files_data[:3]]}")
        else:
            # Log what files were found (if any) to help debug
            all_objects = storage_service.list_all_objects(prefix)  # Will add this debug method
            logger.warning(f"No audio files found. Total objects with prefix '{prefix}': {len(all_objects)}")
            if len(all_objects) > 0:
                logger.warning(f"Sample object keys: {[obj['key'] for obj in all_objects[:5]]}")
        
        files = [S3FileInfo(**f) for f in files_data]
        
        return ListS3FilesResponse(
            files=files,
            count=len(files),
            prefix=prefix
        )
    except Exception as e:
        logger.error(f"Error listing S3 files with prefix '{prefix}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list S3 files: {str(e)}")


@router.post("/batch-import", response_model=BatchImportResponse)
def batch_import_files(request: BatchImportRequest, db: Session = Depends(get_db)):
    """
    Import multiple files from S3. Creates Call records and queues processing for each file.
    Skips files that already exist in database (based on audio_object_key).
    """
    if not request.s3_keys:
        raise HTTPException(status_code=400, detail="No files specified for import")
    
    queued = 0
    skipped = 0
    errors = []
    
    for s3_key in request.s3_keys:
        try:
            # Check if file already exists in database
            existing_call = db.query(Call).filter(Call.audio_object_key == s3_key).first()
            if existing_call:
                skipped += 1
                continue
            
            # Verify file exists in S3
            if not storage_service.object_exists(s3_key):
                errors.append(f"{s3_key}: File not found in S3")
                continue
            
            # Create Call record
            call_id = uuid.uuid4()
            call = Call(
                id=call_id,
                status="PENDING",
                audio_object_key=s3_key
            )
            db.add(call)
            db.commit()
            
            # Queue processing
            process_call_task.delay(str(call.id))
            queued += 1
            
            logger.info(f"Queued S3 file for processing: {s3_key} (call_id: {call_id})")
            
        except Exception as e:
            logger.error(f"Error importing file {s3_key}: {str(e)}", exc_info=True)
            errors.append(f"{s3_key}: {str(e)}")
            db.rollback()
    
    return BatchImportResponse(
        total_files=len(request.s3_keys),
        queued=queued,
        skipped=skipped,
        errors=errors
    )


@router.post("/import-prefix", response_model=BatchImportResponse)
def import_prefix(prefix: str, db: Session = Depends(get_db)):
    """
    Import all audio files from a given S3 prefix. 
    Lists all files in the prefix and queues them for processing.
    """
    try:
        # Normalize prefix
        prefix = prefix.strip()
        if prefix and not prefix.endswith('/') and '/' in prefix:
            prefix = prefix + '/'
        
        # List all files in prefix
        files_data = storage_service.list_objects(prefix)
        
        if not files_data:
            raise HTTPException(status_code=404, detail=f"No audio files found in prefix: {prefix}")
        
        # Extract S3 keys
        s3_keys = [f['key'] for f in files_data]
        
        # Use batch import logic
        queued = 0
        skipped = 0
        errors = []
        
        for s3_key in s3_keys:
            try:
                # Check if file already exists in database
                existing_call = db.query(Call).filter(Call.audio_object_key == s3_key).first()
                if existing_call:
                    skipped += 1
                    continue
                
                # Verify file exists in S3 (should always be true, but double-check)
                if not storage_service.object_exists(s3_key):
                    errors.append(f"{s3_key}: File not found in S3")
                    continue
                
                # Create Call record
                call_id = uuid.uuid4()
                call = Call(
                    id=call_id,
                    status="PENDING",
                    audio_object_key=s3_key
                )
                db.add(call)
                db.commit()
                
                # Queue processing
                process_call_task.delay(str(call.id))
                queued += 1
                
                logger.info(f"Queued S3 file for processing: {s3_key} (call_id: {call_id})")
                
            except Exception as e:
                logger.error(f"Error importing file {s3_key}: {str(e)}", exc_info=True)
                errors.append(f"{s3_key}: {str(e)}")
                db.rollback()
        
        return BatchImportResponse(
            total_files=len(s3_keys),
            queued=queued,
            skipped=skipped,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing prefix {prefix}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to import prefix: {str(e)}")

