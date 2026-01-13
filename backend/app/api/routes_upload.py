from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
from pathlib import Path
from app.db.session import get_db
from app.db.models import Call
from app.services.storage import storage_service
from app.tasks.process_call import process_call_task

router = APIRouter(prefix="/upload", tags=["upload"])


class PresignResponse(BaseModel):
    call_id: str
    object_key: str
    upload_url: str


class CompleteResponse(BaseModel):
    call_id: str
    status: str
    message: str


@router.post("/presign", response_model=PresignResponse)
def presign_upload(
    content_type: str = Query("audio/wav", description="MIME type of the file"),
    filename: str = Query(None, description="Original filename (optional, used to preserve extension)"),
    db: Session = Depends(get_db)
):
    """Generate a presigned PUT URL for uploading audio. Creates a new call record in PENDING status."""
    if filename:
        ext = Path(filename).suffix.lower()
        if not ext:
            ext = None
    else:
        ext = None
    
    if not ext:
        content_type_to_ext = {
            "audio/wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/mp4": ".mp4",
            "audio/m4a": ".m4a",
            "audio/ogg": ".ogg",
            "audio/webm": ".webm",
            "audio/flac": ".flac",
            "audio/x-m4a": ".m4a",
            "audio/x-ms-wma": ".wma",
        }
        ext = content_type_to_ext.get(content_type, ".wav")
    
    call_id = uuid.uuid4()
    object_key = f"upload/{call_id}{ext}"
    
    call = Call(
        id=call_id,
        status="PENDING",
        audio_object_key=object_key
    )
    db.add(call)
    db.commit()
    
    upload_url = storage_service.presign_put(object_key, content_type)
    
    return PresignResponse(
        call_id=str(call_id),
        object_key=object_key,
        upload_url=upload_url
    )


@router.post("/complete/{call_id}", response_model=CompleteResponse)
def complete_upload(call_id: str, db: Session = Depends(get_db)):
    """Mark upload as complete and enqueue processing task."""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if call.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Call is already {call.status}")
    
    if not storage_service.object_exists(call.audio_object_key):
        raise HTTPException(status_code=400, detail="Audio file not found in storage")
    
    process_call_task.delay(str(call.id))
    
    return CompleteResponse(
        call_id=str(call.id),
        status="queued",
        message="Call processing has been queued"
    )

