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


@router.get("/wind-down")
def get_wind_down(db: Session = Depends(get_db)):
    """
    Sleep bucketed by how long before bed the last session ended.
    Answers: "does stopping earlier actually help me sleep?"
    """
    return insights_service.get_wind_down_impact(db)


@router.get("/late-night")
def get_late_night(db: Session = Depends(get_db)):
    """
    Sleep after late-night gaming vs earlier gaming vs no gaming.
    Answers: "is it the gaming, or just the hour I stop?"
    """
    return insights_service.get_late_night_impact(db)


@router.get("/playtime")
def get_playtime(db: Session = Depends(get_db)):
    """
    Next-morning recovery bucketed by how much was played that day
    (<1h / 1–3h / 3h+). Answers: "does a longer night cost more recovery?"
    """
    return insights_service.get_playtime_impact(db)


@router.get("/activity-interaction")
def get_activity_interaction(db: Session = Depends(get_db)):
    """
    Recovery on gaming days that were also physically active vs sedentary vs
    no-gaming days. Answers: "does staying active offset the gaming hit?"
    """
    return insights_service.get_activity_interaction(db)


@router.get("/weekly")
def get_weekly(db: Session = Depends(get_db)):
    """Per-week total gaming minutes vs average next-morning sleep score."""
    return insights_service.get_weekly_playtime_vs_sleep(db)
