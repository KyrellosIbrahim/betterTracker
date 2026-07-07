# Routes for cross-domain insights.
# Correlates game session data with Fitbit health data to surface patterns
# like how different game genres affect heart rate, sleep, and breathing.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import insights_service

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/by-genre")
def get_insights_by_genre(db: Session = Depends(get_db)):
    """
    Average health metrics grouped by game genre.
    Example: avg heart rate during horror vs casual vs competitive sessions.
    """
    return insights_service.get_health_by_genre(db)


@router.get("/sleep-impact")
def get_sleep_impact(db: Session = Depends(get_db)):
    """
    Sleep score comparison across game genres.
    Answers: "Do I sleep worse after playing certain genres?"
    """
    return insights_service.get_sleep_impact_by_genre(db)


@router.get("/by-competitive")
def get_insights_by_competitive(db: Session = Depends(get_db)):
    """
    Average health metrics for competitive vs non-competitive sessions.
    """
    return insights_service.get_health_by_competitive(db)


@router.get("/sleep-impact-competitive")
def get_sleep_impact_competitive(db: Session = Depends(get_db)):
    """
    Sleep score on competitive days vs casual-only days vs no-gaming days.
    Answers: "Do I sleep worse after playing competitive games?"
    """
    return insights_service.get_sleep_impact_by_competitive(db)
