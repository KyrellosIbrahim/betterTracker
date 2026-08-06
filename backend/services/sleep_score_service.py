# Sleep score calculation modeled on the Google Health (Fitbit) sleep score.
#
# Google doesn't publish exact weights, but documents the structure (duration,
# sound sleep, restlessness/interruptions) and — importantly — says the
# algorithm "compares your sleep data against targets tailored to your age,
# gender, and total time you were sleeping", with most users averaging 72-83.
#
# So each sub-metric is scored against *personal* anchors derived from the
# user's own history (see calibrate_sleep_baseline.py), not fixed thresholds.
# A night at the personal 10th percentile earns LOW_FRACTION of a component's
# points, the 90th percentile earns HIGH_FRACTION, linear in between and
# clamped outside. Fixed thresholds saturated badly: with absolute targets
# every night maxed out quality and restoration, leaving the score a proxy
# for duration alone.
#
# Anchors are clamped to sane absolute bounds (see ANCHOR_CLAMPS) so that
# habits drifting worse can't quietly drag the targets down with them.
#
# Not modeled: Google's "time to sound sleep" / sleep-onset latency. The
# Health API reports minutesToFallAsleep as 0 on every session for this
# device, so scoring it would hand out free points.

from sqlalchemy.orm import Session

from database import SessionLocal
from models.sleep_baseline import SleepBaseline

# Points per component (sum to 100). Duration dominates, per Google's
# "total sleep duration makes up the majority of the score".
DURATION_POINTS = 50
DEEP_POINTS = 12.5
REM_POINTS = 12.5
RESTORATION_POINTS = 25

# Fraction of a component's points earned at the personal 10th/90th percentile.
# Calibrated so the score averages ~78 across a typical baseline — the middle
# of Google's published 72-83 range — with enough spread to be discriminating.
LOW_FRACTION = 0.55
HIGH_FRACTION = 0.97

# Population fallback anchors, used until a personal baseline is computed.
DEFAULT_ANCHORS = {
    "duration_minutes": (360.0, 480.0),
    "deep_pct": (0.13, 0.23),
    "rem_pct": (0.15, 0.25),
    "awake_minutes": (5.0, 40.0),
}

# Bounds each personal anchor is clamped into, so the targets stay tied to
# healthy-adult norms even if the user's own history drifts.
ANCHOR_CLAMPS = {
    "duration_minutes": ((300.0, 420.0), (420.0, 480.0)),
    "deep_pct": ((0.10, 0.16), (0.18, 0.25)),
    "rem_pct": ((0.12, 0.18), (0.20, 0.28)),
    "awake_minutes": ((0.0, 10.0), (20.0, 60.0)),
}

# Cached anchors, loaded from the sleep_baseline table on first use.
_anchors_cache: dict | None = None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def percentile(values: list[float], p: float) -> float:
    """Linear-interpolated percentile (p between 0 and 1) of a non-empty list."""
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def load_anchors(db: Session | None = None) -> dict:
    """
    Read the personal anchors from the DB, falling back to population defaults.
    Cached after the first read; call clear_anchor_cache() after recalibrating.
    """
    global _anchors_cache
    if _anchors_cache is not None:
        return _anchors_cache

    owns_session = db is None
    db = db or SessionLocal()
    try:
        row = db.query(SleepBaseline).first()
    finally:
        if owns_session:
            db.close()

    if row is None:
        _anchors_cache = dict(DEFAULT_ANCHORS)
    else:
        _anchors_cache = {
            "duration_minutes": (row.duration_low, row.duration_high),
            "deep_pct": (row.deep_pct_low, row.deep_pct_high),
            "rem_pct": (row.rem_pct_low, row.rem_pct_high),
            "awake_minutes": (row.awake_low, row.awake_high),
        }
    return _anchors_cache


def clear_anchor_cache() -> None:
    """Drop the cached anchors so the next score reload picks up a new baseline."""
    global _anchors_cache
    _anchors_cache = None


def derive_anchors(metrics: list[dict]) -> dict:
    """
    Build personal anchors from a list of per-night metric dicts (as returned by
    extract_metrics). Uses the 10th/90th percentile of each sub-metric, clamped
    to ANCHOR_CLAMPS. Raises ValueError if given no usable nights.
    """
    usable = [m for m in metrics if m and m.get("minutes_asleep")]
    if not usable:
        raise ValueError("no usable sleep sessions to calibrate from")

    samples = {
        "duration_minutes": [m["minutes_asleep"] for m in usable],
        "deep_pct": [m["deep_minutes"] / m["minutes_asleep"] for m in usable],
        "rem_pct": [m["rem_minutes"] / m["minutes_asleep"] for m in usable],
        "awake_minutes": [m["awake_minutes"] for m in usable],
    }

    anchors = {}
    for name, values in samples.items():
        (low_min, low_max), (high_min, high_max) = ANCHOR_CLAMPS[name]
        anchors[name] = (
            _clamp(percentile(values, 0.10), low_min, low_max),
            _clamp(percentile(values, 0.90), high_min, high_max),
        )
    return anchors


def _fraction(value: float, anchors: tuple[float, float], higher_is_better: bool = True) -> float:
    """Map a metric onto [0, 1] using its personal low/high anchors."""
    low, high = anchors
    position = (value - low) / (high - low) if high != low else 1.0
    if not higher_is_better:
        position = 1 - position
    return _clamp(LOW_FRACTION + (HIGH_FRACTION - LOW_FRACTION) * position, 0.0, 1.0)


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


def extract_metrics(sleep_data: dict) -> dict | None:
    """
    Pull the raw per-night metrics out of a Google Health sleep response.
    Returns None when the response has no usable sleep session.
    """
    session = _pick_main_session(sleep_data)
    if not session:
        return None

    summary = session.get("summary", {})
    minutes_asleep = _minutes(summary, "minutesAsleep")
    if minutes_asleep <= 0:
        return None

    stages = _stage_minutes(summary)
    minutes_in_period = _minutes(summary, "minutesInSleepPeriod")
    return {
        "minutes_asleep": minutes_asleep,
        "minutes_in_sleep_period": minutes_in_period,
        "deep_minutes": stages.get("DEEP", 0),
        "light_minutes": stages.get("LIGHT", 0),
        "rem_minutes": stages.get("REM", 0),
        "awake_minutes": stages.get("AWAKE", 0),
        "efficiency": round(minutes_asleep / minutes_in_period, 3) if minutes_in_period else None,
        "has_stages": session.get("type") == "STAGES"
        and bool(stages.get("DEEP", 0) or stages.get("REM", 0)),
    }


def score_metrics(metrics: dict, anchors: dict | None = None) -> dict:
    """
    Score a night from its extracted metrics. Split out from
    calculate_sleep_score so stored snapshots can be rescored without
    refetching the raw API response.
    """
    anchors = anchors or load_anchors()
    minutes_asleep = metrics["minutes_asleep"]

    duration_score = _fraction(minutes_asleep, anchors["duration_minutes"]) * DURATION_POINTS
    restoration_score = (
        _fraction(metrics["awake_minutes"], anchors["awake_minutes"], higher_is_better=False)
        * RESTORATION_POINTS
    )

    # Devices that only report classic (no-stage) sleep can't be scored on
    # stage composition — fold quality's points into the components we do have.
    if metrics.get("has_stages", True):
        deep_pct = metrics["deep_minutes"] / minutes_asleep
        rem_pct = metrics["rem_minutes"] / minutes_asleep
        quality_score = (
            _fraction(deep_pct, anchors["deep_pct"]) * DEEP_POINTS
            + _fraction(rem_pct, anchors["rem_pct"]) * REM_POINTS
        )
    else:
        stageless_points = DEEP_POINTS + REM_POINTS
        duration_share = DURATION_POINTS / (DURATION_POINTS + RESTORATION_POINTS)
        quality_score = (
            duration_score / DURATION_POINTS * stageless_points * duration_share
            + restoration_score / RESTORATION_POINTS * stageless_points * (1 - duration_share)
        )

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
            "minutes_in_sleep_period": metrics.get("minutes_in_sleep_period"),
            "deep_minutes": int(metrics["deep_minutes"]),
            "light_minutes": int(metrics.get("light_minutes", 0)),
            "rem_minutes": int(metrics["rem_minutes"]),
            "awake_minutes": int(metrics["awake_minutes"]),
            "efficiency": metrics.get("efficiency"),
        },
    }


def calculate_sleep_score(sleep_data: dict, anchors: dict | None = None) -> dict | None:
    """
    Compute a 0-100 sleep score from a Google Health API sleep response.
    Returns the total score, rating band, per-component breakdown, and the
    raw metrics used, or None if the response has no sleep session.
    """
    metrics = extract_metrics(sleep_data)
    if metrics is None:
        return None
    return score_metrics(metrics, anchors)
