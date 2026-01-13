from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.db.session import get_db
from app.db.models import Call

router = APIRouter(prefix="/calls", tags=["calls"])


class CallResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    audio_object_key: str
    duration_sec: Optional[float] = None

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    text: str
    model: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    sentiment: str
    topic: str
    problem_resolved: bool
    summary: str
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CallDetailResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    audio_object_key: str
    duration_sec: Optional[float] = None
    transcript: Optional[TranscriptResponse] = None
    analysis: Optional[AnalysisResponse] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[CallResponse])
def list_calls(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """
    List the most recent calls with pagination support.
    
    Args:
        limit: Number of calls to return (default: 10)
        offset: Number of calls to skip (default: 0)
    """
    calls = db.query(Call).order_by(Call.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        CallResponse(
            id=str(call.id),
            status=call.status,
            created_at=call.created_at,
            audio_object_key=call.audio_object_key,
            duration_sec=call.duration_sec
        )
        for call in calls
    ]


@router.get("/{call_id}", response_model=CallDetailResponse)
def get_call_detail(call_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific call, including transcript and analysis.
    """
    try:
        call_uuid = UUID(call_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid call ID format")
    
    # Query call with related transcript and analysis using joinedload for efficiency
    call = db.query(Call).options(
        joinedload(Call.transcript),
        joinedload(Call.analysis)
    ).filter(Call.id == call_uuid).first()
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    # Build response with transcript and analysis if available
    transcript_data = None
    if call.transcript:
        transcript_data = TranscriptResponse(
            text=call.transcript.text,
            model=call.transcript.model,
            created_at=call.transcript.created_at
        )
    
    analysis_data = None
    if call.analysis:
        analysis_data = AnalysisResponse(
            sentiment=call.analysis.sentiment,
            topic=call.analysis.topic,
            problem_resolved=call.analysis.problem_resolved,
            summary=call.analysis.summary,
            confidence=call.analysis.confidence,
            created_at=call.analysis.created_at
        )
    
    return CallDetailResponse(
        id=str(call.id),
        status=call.status,
        created_at=call.created_at,
        audio_object_key=call.audio_object_key,
        duration_sec=call.duration_sec,
        transcript=transcript_data,
        analysis=analysis_data
    )

