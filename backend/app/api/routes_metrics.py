from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, Integer, case
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from app.db.session import get_db
from app.db.models import Call, Analysis

router = APIRouter(prefix="/metrics", tags=["metrics"])


class TopicCount(BaseModel):
    topic: str
    count: int


class TopicNegativity(BaseModel):
    topic: str
    negative_rate: float


class WeeklySpikeAlert(BaseModel):
    topic: str
    current_week_count: int
    last_week_count: int
    spike_ratio: float
    negative_rate: float
    message: str


class CallStatistics(BaseModel):
    total_calls: int
    done_calls: int
    processing_calls: int
    pending_calls: int
    failed_calls: int
    success_rate: float
    unique_topics: int


@router.get("/call_statistics", response_model=CallStatistics)
def get_call_statistics(db: Session = Depends(get_db)):
    """
    Get total call statistics from ALL calls in database (not paginated).
    Returns counts by status and success rate.
    """
    # Get total count
    total_calls = db.query(func.count(Call.id)).scalar() or 0
    
    # Get counts by status
    done_calls = db.query(func.count(Call.id)).filter(Call.status == "DONE").scalar() or 0
    processing_calls = db.query(func.count(Call.id)).filter(Call.status == "PROCESSING").scalar() or 0
    pending_calls = db.query(func.count(Call.id)).filter(Call.status == "PENDING").scalar() or 0
    failed_calls = db.query(func.count(Call.id)).filter(Call.status == "FAILED").scalar() or 0
    
    # Calculate success rate
    success_rate = (done_calls / total_calls * 100) if total_calls > 0 else 0.0
    
    # Get unique topics count (from completed analyses)
    unique_topics = db.query(func.count(func.distinct(Analysis.topic))).join(Call, Call.id == Analysis.call_id).filter(Call.status == "DONE").scalar() or 0
    
    return CallStatistics(
        total_calls=total_calls,
        done_calls=done_calls,
        processing_calls=processing_calls,
        pending_calls=pending_calls,
        failed_calls=failed_calls,
        success_rate=round(success_rate, 2),
        unique_topics=unique_topics
    )


@router.get("/topic_counts", response_model=List[TopicCount])
def get_topic_counts(db: Session = Depends(get_db)):
    """
    Get count of calls by topic.
    """
    results = (
        db.query(Analysis.topic, func.count(Analysis.call_id).label("count"))
        .join(Call, Call.id == Analysis.call_id)
        .filter(Call.status == "DONE")
        .group_by(Analysis.topic)
        .order_by(func.count(Analysis.call_id).desc())
        .all()
    )
    
    return [TopicCount(topic=topic, count=count) for topic, count in results]


@router.get("/negativity_by_topic", response_model=List[TopicNegativity])
def get_negativity_by_topic(db: Session = Depends(get_db)):
    """
    Get negative sentiment rate by topic.
    """
    # Get total and negative counts per topic
    results = (
        db.query(
            Analysis.topic,
            func.count(Analysis.call_id).label("total"),
            func.sum(
                case((Analysis.sentiment == "negative", 1), else_=0).cast(Integer)
            ).label("negative")
        )
        .join(Call, Call.id == Analysis.call_id)
        .filter(Call.status == "DONE")
        .group_by(Analysis.topic)
        .all()
    )
    
    return [
        TopicNegativity(
            topic=topic,
            negative_rate=round(float(negative or 0) / total, 2) if total > 0 else 0.0
        )
        for topic, total, negative in results
    ]


@router.get("/weekly_spikes", response_model=List[WeeklySpikeAlert])
def get_weekly_spikes(db: Session = Depends(get_db)):
    """
    Detect topics with significant week-over-week spikes and high negativity.
    Alert when current week count > last week * 1.4 AND negative rate > 0.6
    """
    try:
        now = datetime.utcnow()
        current_week_start = now - timedelta(days=7)
        last_week_start = current_week_start - timedelta(days=7)
        
        # Get current week stats
        current_week_stats = (
            db.query(
                Analysis.topic,
                func.count(Analysis.call_id).label("count"),
                func.sum(
                    case((Analysis.sentiment == "negative", 1), else_=0).cast(Integer)
                ).label("negative")
            )
            .join(Call, Call.id == Analysis.call_id)
            .filter(
                and_(
                    Call.status == "DONE",
                    Call.created_at >= current_week_start
                )
            )
            .group_by(Analysis.topic)
            .all()
        )
        
        # Get last week stats
        last_week_stats = (
            db.query(
                Analysis.topic,
                func.count(Analysis.call_id).label("count")
            )
            .join(Call, Call.id == Analysis.call_id)
            .filter(
                and_(
                    Call.status == "DONE",
                    Call.created_at >= last_week_start,
                    Call.created_at < current_week_start
                )
            )
            .group_by(Analysis.topic)
            .all()
        )
        
        # Build lookup for last week
        last_week_map = {topic: count for topic, count in last_week_stats}
        
        alerts = []
        for topic, current_count, negative_count in current_week_stats:
            last_count = last_week_map.get(topic, 0)
            negative_rate = float(negative_count or 0) / current_count if current_count > 0 else 0.0
            
            # Check spike condition
            if last_count > 0:
                spike_ratio = current_count / last_count
            else:
                spike_ratio = float('inf') if current_count > 0 else 1.0
            
            # Alert if spike > 1.4x and negative rate > 60%
            if spike_ratio > 1.4 and negative_rate > 0.6:
                # Handle infinity case (new topic with no previous week data)
                if spike_ratio == float('inf'):
                    spike_message = "new topic"
                    spike_ratio_value = 999.0  # Use a high value for display
                else:
                    spike_pct = int(spike_ratio * 100 - 100)
                    spike_message = f"{spike_pct}% increase"
                    spike_ratio_value = round(spike_ratio, 2)
                
                alerts.append(
                    WeeklySpikeAlert(
                        topic=topic,
                        current_week_count=current_count,
                        last_week_count=last_count,
                        spike_ratio=spike_ratio_value,
                        negative_rate=round(negative_rate, 2),
                        message=f"⚠️ {topic.replace('_', ' ').title()}: {spike_message} with {int(negative_rate * 100)}% negative sentiment"
                    )
                )
        
        return alerts
    except Exception as e:
        # Log error but return empty list to avoid breaking frontend
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting weekly spikes: {str(e)}", exc_info=True)
        return []  # Return empty list instead of raising error
