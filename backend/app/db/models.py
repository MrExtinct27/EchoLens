from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.session import Base


class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default="PENDING")  # PENDING, PROCESSING, DONE, FAILED
    audio_object_key = Column(String, nullable=False)
    duration_sec = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transcript = relationship("Transcript", back_populates="call", uselist=False, cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="call", uselist=False, cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"

    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    text = Column(String, nullable=False)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    call = relationship("Call", back_populates="transcript")


class Analysis(Base):
    __tablename__ = "analyses"

    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True)
    sentiment = Column(String, nullable=False)  # negative, neutral, positive
    topic = Column(String, nullable=False)  # billing_issue, tech_support, cancellation, shipping, other
    problem_resolved = Column(Boolean, nullable=False)
    summary = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    call = relationship("Call", back_populates="analysis")

