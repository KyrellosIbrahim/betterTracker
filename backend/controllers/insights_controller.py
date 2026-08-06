# Routes for cross-domain insights.
# Correlates game session data with Google Health data.
#
# All of these join a gaming session to the FOLLOWING morning's health
# snapshot, and treat a "gaming day" as running from 4am to 4am so late-night
# sessions land on the right evening. See services/insights_service.py.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import insights_service

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/by-genre")
def get_insights_by_genre(db: Session = Depends(get_db)):
    """
    Next-morning health metrics grouped by game genre.
    Example: recovery after horror vs casual vs competitive sessions.
    """
    return insights_service.get_health_by_genre(db)


@router.get("/sleep-impact")
def get_sleep_impact(db: Session = Depends(get_db)):
    """
    Next-morning sleep score after each genre, best first.
    Answers: "which genres precede my worst sleep?"
    """
    return insights_service.get_sleep_impact_by_genre(db)


@router.get("/by-competitive")
def get_insights_by_competitive(db: Session = Depends(get_db)):
    """Next-morning health metrics for competitive vs non-competitive play."""
    return insights_service.get_health_by_competitive(db)


@router.get("/sleep-impact-competitive")
def get_sleep_impact_competitive(db: Session = Depends(get_db)):
    """
    Sleep after competitive nights vs casual-only nights vs no-gaming nights.
    Answers: "do I sleep worse after playing competitive games?"
    """
    return insights_service.get_sleep_impact_by_competitive(db)
