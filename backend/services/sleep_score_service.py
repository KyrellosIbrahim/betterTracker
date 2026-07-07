# Sleep score calculation modeled on the Google Health (Fitbit) sleep score.
# Google doesn't publish exact weights, but documents the structure: the score
# sums duration, quality (deep + REM stages), and restoration (efficiency,
# restlessness, time to fall asleep) sub-scores out of 100, with rating bands
# Excellent 90-100 / Good 80-89 / Fair 60-79 / Poor <60.
#
# Weighting follows the widely reported Fitbit split: duration ~50%, stage
# quality ~25%, restoration ~25%. Restoration here uses sleep efficiency and
# sleep-onset latency; Fitbit also factors sleeping-vs-resting heart rate,
# which the Health API sleep endpoint doesn't expose.

# Points per component (sum to 100).
DURATION_POINTS = 50
DEEP_POINTS = 12.5
REM_POINTS = 12.5
EFFICIENCY_POINTS = 15
LATENCY_POINTS = 10

# Benchmarks. Duration target matches Fitbit's 8h recommendation; deep and REM
# targets are the low end of typical healthy-adult stage shares (15% / 20%);
# 90% efficiency and <=20 min sleep-onset latency are standard clinical norms.
DURATION_TARGET_MINUTES = 480
DEEP_TARGET_PCT = 0.15
REM_TARGET_PCT = 0.20
EFFICIENCY_TARGET = 0.90
LATENCY_FULL_CREDIT_MINUTES = 20
LATENCY_ZERO_CREDIT_MINUTES = 60


def _rating(score: int) -> str:
    """Map a score to Google Health's published rating bands."""
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "good"
    if score >= 60:
        return "fair"
    return "poor"


def _minutes(container: dict, key: str) -> float:
    """Read a minutes field, coercing to float (the API serializes int64 as strings)."""
    try:
        return float(container.get(key) or 0)
    except (TypeError, ValueError):
        return 0.0


def _stage_minutes(summary: dict) -> dict:
    """Extract minutes per stage type from the summary's stagesSummary list."""
    return {stage.get("type"): _minutes(stage, "minutes") for stage in summary.get("stagesSummary", [])}


def _pick_main_session(sleep_data: dict) -> dict | None:
    """Pick the primary sleep session (longest non-nap) from the API response."""
    sessions = [
        dp["sleep"]
        for dp in sleep_data.get("dataPoints", [])
        if "sleep" in dp and not dp["sleep"].get("metadata", {}).get("nap")
    ]
    if not sessions:
        return None
    return max(sessions, key=lambda s: _minutes(s.get("summary", {}), "minutesAsleep"))


def calculate_sleep_score(sleep_data: dict) -> dict | None:
    """
    Compute a 0-100 sleep score from a Google Health API sleep response.
    Returns the total score, rating band, per-component breakdown, and the
    raw metrics used, or None if the response has no sleep session.
    """
    session = _pick_main_session(sleep_data)
    if not session:
        return None

    summary = session.get("summary", {})
    minutes_asleep = _minutes(summary, "minutesAsleep")
    minutes_in_period = _minutes(summary, "minutesInSleepPeriod")
    minutes_to_fall_asleep = _minutes(summary, "minutesToFallAsleep")
    stages = _stage_minutes(summary)
    deep_minutes = stages.get("DEEP", 0)
    rem_minutes = stages.get("REM", 0)
    has_stages = session.get("type") == "STAGES" and (deep_minutes or rem_minutes)

    if minutes_asleep <= 0:
        return None

    # Duration: linear credit toward the 8h target, capped at full points.
    duration_score = min(minutes_asleep / DURATION_TARGET_MINUTES, 1.0) * DURATION_POINTS

    # Quality: deep and REM shares of total sleep vs their targets. Devices
    # that only report classic (no stages) sleep get quality credit from
    # efficiency instead, mirroring Fitbit's behavior for stage-less trackers.
    efficiency = minutes_asleep / minutes_in_period if minutes_in_period else 1.0
    efficiency_ratio = min(efficiency / EFFICIENCY_TARGET, 1.0)
    if has_stages:
        deep_score = min((deep_minutes / minutes_asleep) / DEEP_TARGET_PCT, 1.0) * DEEP_POINTS
        rem_score = min((rem_minutes / minutes_asleep) / REM_TARGET_PCT, 1.0) * REM_POINTS
        quality_score = deep_score + rem_score
    else:
        quality_score = efficiency_ratio * (DEEP_POINTS + REM_POINTS)

    # Restoration: sleep efficiency (interruptions + restlessness) plus
    # sleep-onset latency, with full latency credit at <=20 min.
    efficiency_score = efficiency_ratio * EFFICIENCY_POINTS
    if minutes_to_fall_asleep <= LATENCY_FULL_CREDIT_MINUTES:
        latency_score = LATENCY_POINTS
    else:
        latency_range = LATENCY_ZERO_CREDIT_MINUTES - LATENCY_FULL_CREDIT_MINUTES
        overshoot = minutes_to_fall_asleep - LATENCY_FULL_CREDIT_MINUTES
        latency_score = max(1 - overshoot / latency_range, 0.0) * LATENCY_POINTS
    restoration_score = efficiency_score + latency_score

    total = round(duration_score + quality_score + restoration_score)

    return {
        "score": total,
        "rating": _rating(total),
        "components": {
            "duration": round(duration_score, 1),
            "quality": round(quality_score, 1),
            "restoration": round(restoration_score, 1),
        },
        "metrics": {
            "minutes_asleep": minutes_asleep,
            "minutes_in_sleep_period": minutes_in_period,
            "minutes_to_fall_asleep": minutes_to_fall_asleep,
            "deep_minutes": int(deep_minutes),
            "light_minutes": int(stages.get("LIGHT", 0)),
            "rem_minutes": int(rem_minutes),
            "awake_minutes": int(stages.get("AWAKE", 0)),
            "efficiency": round(efficiency, 3),
        },
    }
