from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, Integer, case, extract
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging
from app.db.session import get_db
from app.db.models import Call, Analysis
from app.core.config import settings
from groq import Groq

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

# In-memory cache for executive summaries (week-based)
# Format: {week_key: {"summary": str, "last_updated": datetime, "latest_call_timestamp": datetime}}
_executive_summary_cache = {}


class TopicTrend(BaseModel):
    topic: str
    weekly_counts: List[int]
    weekly_negative_rates: List[float]
    trend: str
    pct_change: float


class ResolutionEffectiveness(BaseModel):
    topic: str
    resolution_rate: float
    negative_rate: float
    avg_confidence: float


class EscalationRisk(BaseModel):
    topic: str
    risk_score: float
    drivers: List[str]


class ExecutiveSummary(BaseModel):
    summary: str


def get_iso_week(date: datetime) -> tuple:
    """Get ISO year and week number."""
    year, week, _ = date.isocalendar()
    return year, week


@router.get("/topic_trends", response_model=List[TopicTrend])
def get_topic_trends(weeks: int = Query(8, ge=1, le=52), db: Session = Depends(get_db)):
    """Get weekly topic trend analysis with counts and negative rates."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(weeks=weeks)
    
    completed_calls = (
        db.query(Analysis, Call.created_at)
        .join(Call, Call.id == Analysis.call_id)
        .filter(
            and_(
                Call.status == "DONE",
                Call.created_at >= start_date
            )
        )
        .all()
    )
    
    topic_data = {}
    for analysis, created_at in completed_calls:
        topic = analysis.topic
        if topic not in topic_data:
            topic_data[topic] = {}
        
        year, week = get_iso_week(created_at)
        week_key = f"{year}-W{week:02d}"
        
        if week_key not in topic_data[topic]:
            topic_data[topic][week_key] = {"count": 0, "negative": 0}
        
        topic_data[topic][week_key]["count"] += 1
        if analysis.sentiment == "negative":
            topic_data[topic][week_key]["negative"] += 1
    
    result = []
    for topic, weeks_data in topic_data.items():
        week_keys = sorted(weeks_data.keys())
        weekly_counts = [weeks_data[key]["count"] for key in week_keys]
        weekly_negative_rates = [
            round(weeks_data[key]["negative"] / weeks_data[key]["count"], 2)
            if weeks_data[key]["count"] > 0 else 0.0
            for key in week_keys
        ]
        
        if len(weekly_counts) >= 2:
            current = weekly_counts[-1]
            previous = weekly_counts[-2]
            pct_change = (current - previous) / max(previous, 1)
            
            if pct_change > 0.15:
                trend = "up"
            elif pct_change < -0.15:
                trend = "down"
            else:
                trend = "flat"
        else:
            pct_change = 0.0
            trend = "flat"
        
        result.append(TopicTrend(
            topic=topic,
            weekly_counts=weekly_counts,
            weekly_negative_rates=weekly_negative_rates,
            trend=trend,
            pct_change=round(pct_change, 2)
        ))
    
    return sorted(result, key=lambda x: x.topic)


@router.get("/resolution_effectiveness", response_model=List[ResolutionEffectiveness])
def get_resolution_effectiveness(db: Session = Depends(get_db)):
    """Get resolution effectiveness metrics by topic."""
    results = (
        db.query(
            Analysis.topic,
            func.count(Analysis.call_id).label("total"),
            func.sum(
                case((Analysis.problem_resolved == True, 1), else_=0).cast(Integer)
            ).label("resolved"),
            func.sum(
                case((Analysis.sentiment == "negative", 1), else_=0).cast(Integer)
            ).label("negative"),
            func.avg(Analysis.confidence).label("avg_confidence")
        )
        .join(Call, Call.id == Analysis.call_id)
        .filter(Call.status == "DONE")
        .group_by(Analysis.topic)
        .all()
    )
    
    return [
        ResolutionEffectiveness(
            topic=topic,
            resolution_rate=round(float(resolved or 0) / total, 2) if total > 0 else 0.0,
            negative_rate=round(float(negative or 0) / total, 2) if total > 0 else 0.0,
            avg_confidence=round(float(avg_confidence or 0.0), 2)
        )
        for topic, total, resolved, negative, avg_confidence in results
    ]


@router.get("/escalation_risk", response_model=List[EscalationRisk])
def get_escalation_risk(db: Session = Depends(get_db)):
    """Calculate escalation risk score for each topic based on multiple factors."""
    now = datetime.utcnow()
    current_week_start = now - timedelta(days=7)
    last_week_start = current_week_start - timedelta(days=7)
    
    resolution_stats = (
        db.query(
            Analysis.topic,
            func.count(Analysis.call_id).label("total"),
            func.sum(
                case((Analysis.problem_resolved == True, 1), else_=0).cast(Integer)
            ).label("resolved"),
            func.sum(
                case((Analysis.sentiment == "negative", 1), else_=0).cast(Integer)
            ).label("negative")
        )
        .join(Call, Call.id == Analysis.call_id)
        .filter(Call.status == "DONE")
        .group_by(Analysis.topic)
        .all()
    )
    
    current_week_counts = (
        db.query(
            Analysis.topic,
            func.count(Analysis.call_id).label("count")
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
    
    last_week_counts = (
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
    
    last_week_map = {topic: count for topic, count in last_week_counts}
    current_week_map = {topic: count for topic, count in current_week_counts}
    
    result = []
    for topic, total, resolved, negative in resolution_stats:
        resolution_rate = float(resolved or 0) / total if total > 0 else 0.0
        negative_rate = float(negative or 0) / total if total > 0 else 0.0
        
        current_count = current_week_map.get(topic, 0)
        last_count = last_week_map.get(topic, 0)
        
        if last_count > 0:
            weekly_growth = (current_count - last_count) / last_count
        else:
            weekly_growth = 0.0
        
        risk_score = 0.0
        drivers = []
        
        if negative_rate > 0.6:
            risk_score += 0.4
            drivers.append(f"Negative sentiment above 60% ({int(negative_rate * 100)}%)")
        
        if resolution_rate < 0.4:
            risk_score += 0.3
            drivers.append(f"Resolution rate below 40% ({int(resolution_rate * 100)}%)")
        
        if weekly_growth > 0.3:
            risk_score += 0.3
            drivers.append(f"Week-over-week growth above 30% ({int(weekly_growth * 100)}%)")
        
        risk_score = min(risk_score, 1.0)
        
        if not drivers:
            drivers.append("No significant risk factors detected")
        
        result.append(EscalationRisk(
            topic=topic,
            risk_score=round(risk_score, 2),
            drivers=drivers
        ))
    
    return sorted(result, key=lambda x: x.risk_score, reverse=True)


@router.get("/executive_summary", response_model=ExecutiveSummary)
def get_executive_summary(db: Session = Depends(get_db)):
    """
    Generate AI-powered executive summary from computed metrics.
    Summary is cached weekly and only regenerates when new data is added (new calls processed).
    """
    try:
        now = datetime.utcnow()
        # Use ISO week for caching (year-week)
        year, week, _ = now.isocalendar()
        week_key = f"{year}-W{week:02d}"
        
        # Get the most recent call timestamp to detect new data
        latest_call = db.query(func.max(Call.created_at)).filter(Call.status == "DONE").scalar()
        
        # Check if we have a cached summary for this week
        if week_key in _executive_summary_cache:
            cache_entry = _executive_summary_cache[week_key]
            cached_latest_timestamp = cache_entry.get("latest_call_timestamp")
            
            # Only regenerate if new data has been added since cache was created
            if latest_call and cached_latest_timestamp:
                # Compare timestamps - if latest call is newer than cache timestamp, regenerate
                if latest_call <= cached_latest_timestamp:
                    # No new data, return cached summary
                    logger.info(f"Returning cached executive summary for week {week_key}")
                    return ExecutiveSummary(summary=cache_entry["summary"])
            elif not latest_call:
                # No calls at all, return cached summary
                logger.info(f"Returning cached executive summary for week {week_key} (no calls)")
                return ExecutiveSummary(summary=cache_entry["summary"])
        
        # No cache or new data detected - generate new summary
        logger.info(f"Generating new executive summary for week {week_key}")
        
        current_week_start = now - timedelta(days=7)
        last_week_start = current_week_start - timedelta(days=7)
        
        resolution_stats = (
            db.query(
                Analysis.topic,
                func.count(Analysis.call_id).label("total"),
                func.sum(
                    case((Analysis.problem_resolved == True, 1), else_=0).cast(Integer)
                ).label("resolved"),
                func.sum(
                    case((Analysis.sentiment == "negative", 1), else_=0).cast(Integer)
                ).label("negative")
            )
            .join(Call, Call.id == Analysis.call_id)
            .filter(Call.status == "DONE")
            .group_by(Analysis.topic)
            .all()
        )
        
        resolution_map = {}
        for topic, total, resolved, negative in resolution_stats:
            resolution_map[topic] = {
                "resolution_rate": float(resolved or 0) / total if total > 0 else 0.0,
                "negative_rate": float(negative or 0) / total if total > 0 else 0.0
            }
        
        topic_trends_data = {}
        trend_end_date = datetime.utcnow()
        trend_start_date = trend_end_date - timedelta(weeks=2)
        trend_calls = (
            db.query(Analysis, Call.created_at)
            .join(Call, Call.id == Analysis.call_id)
            .filter(
                and_(
                    Call.status == "DONE",
                    Call.created_at >= trend_start_date
                )
            )
            .all()
        )
        
        for analysis, created_at in trend_calls:
            topic = analysis.topic
            year, week = get_iso_week(created_at)
            week_key = f"{year}-W{week:02d}"
            
            if topic not in topic_trends_data:
                topic_trends_data[topic] = {}
            if week_key not in topic_trends_data[topic]:
                topic_trends_data[topic][week_key] = 0
            topic_trends_data[topic][week_key] += 1
        
        current_week_counts_risk = (
            db.query(
                Analysis.topic,
                func.count(Analysis.call_id).label("count")
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
        
        last_week_counts_risk = (
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
        
        last_week_map_risk = {topic: count for topic, count in last_week_counts_risk}
        current_week_map_risk = {topic: count for topic, count in current_week_counts_risk}
        
        escalation_risks_data = []
        for topic, total, resolved, negative in resolution_stats:
            resolution_rate = float(resolved or 0) / total if total > 0 else 0.0
            negative_rate = float(negative or 0) / total if total > 0 else 0.0
            
            current_count = current_week_map_risk.get(topic, 0)
            last_count = last_week_map_risk.get(topic, 0)
            
            if last_count > 0:
                weekly_growth = (current_count - last_count) / last_count
            else:
                weekly_growth = 0.0
            
            risk_score = 0.0
            if negative_rate > 0.6:
                risk_score += 0.4
            if resolution_rate < 0.4:
                risk_score += 0.3
            if weekly_growth > 0.3:
                risk_score += 0.3
            
            risk_score = min(risk_score, 1.0)
            
            escalation_risks_data.append({
                "topic": topic,
                "risk_score": round(risk_score, 2)
            })
        
        escalation_risks_data = sorted(escalation_risks_data, key=lambda x: x["risk_score"], reverse=True)
        
        current_week_counts = (
            db.query(
                Analysis.topic,
                func.count(Analysis.call_id).label("count")
            )
            .join(Call, Call.id == Analysis.call_id)
            .filter(
                and_(
                    Call.status == "DONE",
                    Call.created_at >= current_week_start
                )
            )
            .group_by(Analysis.topic)
            .order_by(func.count(Analysis.call_id).desc())
            .all()
        )
        
        total_current = sum(count for _, count in current_week_counts)
        total_negative = (
            db.query(func.count(Analysis.call_id))
            .join(Call, Call.id == Analysis.call_id)
            .filter(
                and_(
                    Call.status == "DONE",
                    Call.created_at >= current_week_start,
                    Analysis.sentiment == "negative"
                )
            )
            .scalar() or 0
        )
        
        overall_negative_rate = round(float(total_negative) / total_current, 2) if total_current > 0 else 0.0
        
        top_topics = [{"topic": topic, "count": count} for topic, count in current_week_counts[:5]]
        
        fastest_growing = None
        fastest_growing_pct = 0.0
        for topic, weeks_data in topic_trends_data.items():
            week_keys = sorted(weeks_data.keys())
            if len(week_keys) >= 2:
                current = weeks_data[week_keys[-1]]
                previous = weeks_data[week_keys[-2]]
                if previous > 0:
                    pct_change = (current - previous) / previous
                    if pct_change > fastest_growing_pct:
                        fastest_growing_pct = pct_change
                        fastest_growing = {"topic": topic, "pct_change": pct_change}
        
        most_negative = None
        for topic, stats in resolution_map.items():
            if most_negative is None or stats["negative_rate"] > most_negative["negative_rate"]:
                most_negative = {"topic": topic, "negative_rate": stats["negative_rate"]}
        
        highest_risk = [
            {"topic": risk["topic"], "risk_score": risk["risk_score"]}
            for risk in escalation_risks_data[:3]
            if risk["risk_score"] >= 0.6
        ]
        
        # Calculate overall resolution rate
        total_resolved = sum(
            float(resolved or 0) for _, _, resolved, _ in resolution_stats
        )
        total_all_calls = sum(total for _, total, _, _ in resolution_stats)
        overall_resolution_rate = round(float(total_resolved) / total_all_calls, 2) if total_all_calls > 0 else 0.0
        
        # Get top topics with their details
        top_topics_detailed = []
        for topic_item in top_topics:
            topic = topic_item["topic"]
            count = topic_item["count"]
            topic_stats = resolution_map.get(topic, {})
            top_topics_detailed.append({
                "topic": topic,
                "count": count,
                "negative_rate": topic_stats.get("negative_rate", 0.0),
                "resolution_rate": topic_stats.get("resolution_rate", 0.0)
            })
        
        metrics_input = {
            "time_window": "Last 7 days vs previous 7 days",
            "total_calls": total_current,
            "overall_negative_rate": overall_negative_rate,
            "overall_resolution_rate": overall_resolution_rate,
            "top_topics": top_topics_detailed,
            "fastest_growing_topic": fastest_growing,
            "most_negative_topic": most_negative,
            "highest_risk_topics": highest_risk
        }
        
        api_key = (settings.GROQ_API_KEY or "").strip()
        if not api_key or len(api_key) < 10 or not api_key.startswith("gsk_"):
            return ExecutiveSummary(summary=_generate_deterministic_summary(metrics_input))
        
        try:
            client = Groq(api_key=api_key)
            
            system_prompt = """You are a customer support analytics expert. Generate a detailed, insightful executive summary based on structured metrics data.

Rules:
- Use ONLY the provided metrics (no assumptions or external knowledge)
- Summary must be 4-6 sentences with specific details
- Professional, executive-level tone
- Include specific numbers, percentages, and topic names
- Highlight key trends, risks, and actionable insights
- Mention top topics by volume, fastest growing issues, highest negative sentiment, and escalation risks
- Connect metrics to business impact (e.g., "X% negative sentiment indicates customer dissatisfaction")
- Return ONLY valid JSON with a "summary" field, no markdown, no prose"""

            user_prompt = f"""Generate a detailed executive summary based on these customer support metrics:

{json.dumps(metrics_input, indent=2)}

Provide a comprehensive 4-6 sentence summary that:
1. Opens with overall call volume and sentiment trends
2. Highlights the top 2-3 topics by volume with their specific metrics
3. Mentions fastest growing topic with percentage change
4. Identifies highest negative sentiment topic with specific rate
5. Addresses escalation risks if any high-risk topics exist
6. Concludes with overall resolution rate and key takeaway

Return ONLY valid JSON:
{{
  "summary": "Your detailed 4-6 sentence executive summary here"
}}"""

            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_completion_tokens=500,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            json_text = _extract_json(response_text)
            data = json.loads(json_text)
            
            summary = data.get("summary", "").strip()
            if not summary:
                raise ValueError("Empty summary in LLM response")
            
            # Cache the summary with current week key and latest call timestamp
            _executive_summary_cache[week_key] = {
                "summary": summary,
                "last_updated": now,
                "latest_call_timestamp": latest_call
            }
            
            # Clean up old cache entries (keep only last 4 weeks)
            weeks_to_keep = 4
            if len(_executive_summary_cache) > weeks_to_keep:
                sorted_keys = sorted(_executive_summary_cache.keys(), reverse=True)
                for old_key in sorted_keys[weeks_to_keep:]:
                    del _executive_summary_cache[old_key]
            
            return ExecutiveSummary(summary=summary)
            
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}. Using deterministic fallback.")
            deterministic_summary = _generate_deterministic_summary(metrics_input)
            
            # Cache the deterministic summary as well
            _executive_summary_cache[week_key] = {
                "summary": deterministic_summary,
                "last_updated": now,
                "latest_call_timestamp": latest_call
            }
            
            # Clean up old cache entries (keep only last 4 weeks)
            weeks_to_keep = 4
            if len(_executive_summary_cache) > weeks_to_keep:
                sorted_keys = sorted(_executive_summary_cache.keys(), reverse=True)
                for old_key in sorted_keys[weeks_to_keep:]:
                    del _executive_summary_cache[old_key]
            
            return ExecutiveSummary(summary=deterministic_summary)
            
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}", exc_info=True)
        
        # If we have a cached summary, return it even on error
        if week_key in _executive_summary_cache:
            logger.info(f"Error occurred, returning cached summary for week {week_key}")
            return ExecutiveSummary(summary=_executive_summary_cache[week_key]["summary"])
        
        error_summary = "Unable to generate summary at this time. Please check analytics endpoints."
        return ExecutiveSummary(summary=error_summary)


def _extract_json(text: str) -> str:
    """Extract JSON from text, handling markdown code blocks."""
    import re
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return text.strip()


def _generate_deterministic_summary(metrics: dict) -> str:
    """Generate a detailed deterministic summary when LLM is unavailable."""
    parts = []
    
    total_calls = metrics.get("total_calls", 0)
    overall_negative = metrics.get("overall_negative_rate", 0.0)
    overall_resolution = metrics.get("overall_resolution_rate", 0.0)
    
    # Opening: Overall volume and sentiment
    if total_calls > 0:
        parts.append(f"Analyzed {total_calls} customer support calls in the last 7 days, with {int(overall_negative * 100)}% showing negative sentiment and {int(overall_resolution * 100)}% resolution rate.")
    
    # Top topics by volume
    top_topics = metrics.get("top_topics", [])
    if top_topics:
        top_3 = top_topics[:3]
        topic_names = [t["topic"].replace("_", " ").title() for t in top_3]
        topic_counts = [t["count"] for t in top_3]
        if len(topic_names) == 1:
            parts.append(f"The most common issue was {topic_names[0]} with {topic_counts[0]} calls ({int(topic_counts[0]/total_calls*100)}% of total).")
        elif len(topic_names) == 2:
            parts.append(f"The top issues were {topic_names[0]} ({topic_counts[0]} calls, {int(topic_counts[0]/total_calls*100)}%) and {topic_names[1]} ({topic_counts[1]} calls, {int(topic_counts[1]/total_calls*100)}%).")
        else:
            parts.append(f"The top three issues were {topic_names[0]} ({topic_counts[0]} calls), {topic_names[1]} ({topic_counts[1]} calls), and {topic_names[2]} ({topic_counts[2]} calls), accounting for {int(sum(topic_counts[:3])/total_calls*100)}% of all calls.")
    
    # Fastest growing topic
    if metrics.get("fastest_growing_topic"):
        topic = metrics["fastest_growing_topic"]["topic"].replace("_", " ").title()
        pct = int(metrics["fastest_growing_topic"]["pct_change"] * 100)
        parts.append(f"{topic} saw the largest week-over-week increase at {pct}%, indicating a growing concern.")
    
    # Most negative topic
    if metrics.get("most_negative_topic"):
        topic = metrics["most_negative_topic"]["topic"].replace("_", " ").title()
        rate = int(metrics["most_negative_topic"]["negative_rate"] * 100)
        parts.append(f"{topic} exhibited the highest negative sentiment at {rate}%, signaling potential customer dissatisfaction.")
    
    # Escalation risks
    highest_risk = metrics.get("highest_risk_topics", [])
    if highest_risk:
        risk_topics = [r["topic"].replace("_", " ").title() for r in highest_risk]
        risk_scores = [r["risk_score"] for r in highest_risk]
        if len(risk_topics) == 1:
            parts.append(f"{risk_topics[0]} requires immediate attention with a risk score of {risk_scores[0]:.2f}.")
        elif len(risk_topics) == 2:
            parts.append(f"{risk_topics[0]} (risk score: {risk_scores[0]:.2f}) and {risk_topics[1]} (risk score: {risk_scores[1]:.2f}) require immediate attention due to high escalation risk.")
        else:
            parts.append(f"{len(risk_topics)} topics ({', '.join(risk_topics[:2])}, and {risk_topics[2] if len(risk_topics) > 2 else 'others'}) require immediate attention with risk scores above 0.6.")
    
    # Closing: Overall resolution insight
    if overall_resolution < 0.5:
        parts.append(f"With a {int(overall_resolution * 100)}% resolution rate, there is significant room for improvement in first-contact resolution.")
    elif overall_resolution >= 0.7:
        parts.append(f"The {int(overall_resolution * 100)}% resolution rate demonstrates strong support effectiveness.")
    
    if not parts:
        parts.append("Insufficient data for comprehensive analysis. Please upload more call recordings to generate insights.")
    
    return " ".join(parts)

