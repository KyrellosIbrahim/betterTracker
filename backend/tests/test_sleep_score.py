# Tests for the sleep score. Most of these lock in behaviour that was
# discovered by hitting a real bug, not by guessing at edge cases.

from datetime import datetime

import pytest

from conftest import sleep_response
from services import sleep_score_service as s


# --- Parsing the API payload ---

def test_numeric_fields_arrive_as_strings():
    """The API serializes int64 as JSON strings; treating them as ints once 500'd."""
    metrics = s.extract_metrics(sleep_response(minutes_asleep=450, deep=80))
    assert metrics["minutes_asleep"] == 450.0
    assert metrics["deep_minutes"] == 80.0


def test_no_sleep_session_returns_none():
    assert s.extract_metrics({"dataPoints": []}) is None
    assert s.extract_metrics({}) is None
    assert s.calculate_sleep_score({"dataPoints": []}) is None


def test_zero_minutes_asleep_is_not_a_night():
    assert s.extract_metrics(sleep_response(minutes_asleep=0)) is None


def test_naps_are_excluded_even_when_longer():
    """A long nap must not out-rank the real night."""
    night = sleep_response(minutes_asleep=450)
    nap = sleep_response(minutes_asleep=900, nap=True)["dataPoints"][0]
    payload = {"dataPoints": [nap, *night["dataPoints"]]}
    assert s.extract_metrics(payload)["minutes_asleep"] == 450.0


def test_longest_session_wins_among_several():
    short = sleep_response(minutes_asleep=60)["dataPoints"][0]
    long = sleep_response(minutes_asleep=450)["dataPoints"][0]
    assert s.extract_metrics({"dataPoints": [short, long]})["minutes_asleep"] == 450.0


# --- Timezone handling ---

def test_sleep_times_convert_to_local_wall_time():
    """
    04:07Z with a -18000s offset is 23:07 the previous evening. Getting this
    wrong shifts bedtime by 5h and silently corrupts the wind-down insight.
    """
    metrics = s.extract_metrics(sleep_response())
    assert metrics["sleep_start"] == datetime(2026, 8, 4, 23, 7)
    assert metrics["sleep_end"] == datetime(2026, 8, 5, 7, 32)


def test_missing_interval_does_not_explode():
    payload = sleep_response()
    del payload["dataPoints"][0]["sleep"]["interval"]
    metrics = s.extract_metrics(payload)
    assert metrics["sleep_start"] is None and metrics["sleep_end"] is None


# --- has_stages ---

def test_has_stages_requires_actual_stage_data():
    """
    A STAGES-typed session with no deep and no REM must fall back to the
    stage-less path. A misplaced line once made this always-true.
    """
    assert s.extract_metrics(sleep_response())["has_stages"] is True
    assert s.extract_metrics(sleep_response(deep=0, rem=0))["has_stages"] is False
    assert s.extract_metrics(sleep_response(sleep_type="CLASSIC"))["has_stages"] is False


def test_sleep_end_is_a_datetime_not_a_bool():
    """Regression: `_local_time(...) and bool(...)` returned True and broke inserts."""
    assert isinstance(s.extract_metrics(sleep_response())["sleep_end"], datetime)


# --- Scoring ---

def test_score_within_bounds_for_extremes(anchors):
    terrible = s.score_metrics(
        {"minutes_asleep": 1, "deep_minutes": 0, "rem_minutes": 0, "awake_minutes": 500, "has_stages": True},
        anchors,
    )
    superb = s.score_metrics(
        {"minutes_asleep": 900, "deep_minutes": 300, "rem_minutes": 300, "awake_minutes": 0, "has_stages": True},
        anchors,
    )
    assert 0 <= terrible["score"] <= 100 and 0 <= superb["score"] <= 100
    assert terrible["score"] < superb["score"]


def test_longer_sleep_scores_higher(anchors):
    def score(minutes):
        return s.score_metrics(
            {"minutes_asleep": minutes, "deep_minutes": minutes * 0.2, "rem_minutes": minutes * 0.2,
             "awake_minutes": 10, "has_stages": True},
            anchors,
        )["score"]

    assert score(300) < score(400) < score(480)


def test_more_interruptions_score_lower(anchors):
    def score(awake):
        return s.score_metrics(
            {"minutes_asleep": 450, "deep_minutes": 90, "rem_minutes": 90, "awake_minutes": awake, "has_stages": True},
            anchors,
        )["score"]

    assert score(5) > score(30) > score(90)


def test_components_sum_to_total(anchors):
    result = s.score_metrics(
        {"minutes_asleep": 430, "deep_minutes": 85, "rem_minutes": 95, "awake_minutes": 20, "has_stages": True},
        anchors,
    )
    parts = sum(result["components"].values())
    assert abs(parts - result["score"]) <= 0.5


def test_stageless_device_still_scores(anchors):
    """No stage data must not mean a near-zero quality score."""
    result = s.score_metrics(
        {"minutes_asleep": 440, "deep_minutes": 0, "rem_minutes": 0, "awake_minutes": 8, "has_stages": False},
        anchors,
    )
    assert result["components"]["quality"] > 0
    assert 0 <= result["score"] <= 100


@pytest.mark.parametrize(
    "score,band",
    [(100, "excellent"), (90, "excellent"), (89, "good"), (80, "good"),
     (79, "fair"), (60, "fair"), (59, "poor"), (0, "poor")],
)
def test_rating_bands_match_google(score, band):
    assert s._rating(score) == band


# --- Personalized anchors ---

def test_anchors_are_clamped_to_healthy_bounds():
    """
    A month of 3-hour nights must not drag the "full credit" target down to
    3 hours — otherwise the score flatters worsening habits.
    """
    awful = [
        {"minutes_asleep": 180, "deep_minutes": 20, "rem_minutes": 20, "awake_minutes": 60}
        for _ in range(30)
    ]
    derived = s.derive_anchors(awful)
    low, high = derived["duration_minutes"]
    assert low >= s.ANCHOR_CLAMPS["duration_minutes"][0][0]
    assert high >= 420  # still expects a full night for full credit


def test_derive_anchors_needs_data():
    with pytest.raises(ValueError):
        s.derive_anchors([])


def test_percentile_interpolates():
    assert s.percentile([1, 2, 3, 4, 5], 0.5) == 3
    assert s.percentile([10], 0.9) == 10
