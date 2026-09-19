# Locks in the exact Google Health API field names for the Phase 4 metrics
# (steps, active minutes, SpO2, weight). The JSON fixtures below are trimmed
# copies of real API responses captured live — if Google renames a field or we
# mis-map one, these fail instead of silently writing NULLs forever.

from datetime import date

from services import fitbit_service

# --- Real response shapes (trimmed) ---

STEPS_ROLLUP = {"rollupDataPoints": [{"steps": {"countSum": "5305"}}]}
ACTIVE_MINUTES_ROLLUP = {
    "rollupDataPoints": [
        {"activeMinutes": {"activeMinutesRollupByActivityLevel": [
            {"activityLevel": "LIGHT", "activeMinutesSum": "167"},
            {"activityLevel": "MODERATE", "activeMinutesSum": "20"},
        ]}}
    ]
}
SPO2_DAILY = {"dataPoints": [{"dailyOxygenSaturation": {"averagePercentage": 97.1}}]}
WEIGHT_SAMPLES = {
    "dataPoints": [
        {"weight": {"sampleTime": {"physicalTime": "2026-09-17T07:00:00Z"}, "weightGrams": 82000}},
        {"weight": {"sampleTime": {"physicalTime": "2026-09-17T12:33:24Z"}, "weightGrams": 81550}},
    ]
}


# --- Parsers: field names + string→number coercion ---

def test_parse_steps_coerces_string_countsum():
    assert fitbit_service._parse_steps(STEPS_ROLLUP) == 5305


def test_parse_active_minutes_sums_all_levels():
    # 167 (LIGHT) + 20 (MODERATE)
    assert fitbit_service._parse_active_minutes(ACTIVE_MINUTES_ROLLUP) == 187


def test_parse_spo2_reads_average_percentage():
    assert fitbit_service._parse_spo2(SPO2_DAILY) == 97.1


def test_parse_weight_takes_latest_reading_in_kg():
    # Grams → kg, and the later physicalTime (12:33) wins over the earlier (07:00)
    assert fitbit_service._parse_weight(WEIGHT_SAMPLES) == 81.55


def test_parsers_return_none_on_empty():
    assert fitbit_service._parse_steps({"rollupDataPoints": []}) is None
    assert fitbit_service._parse_active_minutes({"rollupDataPoints": []}) is None
    assert fitbit_service._parse_spo2({"dataPoints": []}) is None
    assert fitbit_service._parse_weight({"dataPoints": []}) is None


# --- build_snapshot_data wiring: right response → right column ---

def test_build_snapshot_data_maps_new_metrics(monkeypatch):
    monkeypatch.setattr(fitbit_service, "fetch_resting_heart_rate",
                        lambda d: {"dataPoints": [{"dailyRestingHeartRate": {"beatsPerMinute": 60}}]})
    monkeypatch.setattr(fitbit_service, "fetch_breathing_rate",
                        lambda d: {"dataPoints": [{"dailyRespiratoryRate": {"breathsPerMinute": 15.5}}]})
    monkeypatch.setattr(fitbit_service, "fetch_sleep", lambda d: {})
    monkeypatch.setattr(fitbit_service.sleep_score_service, "calculate_sleep_score", lambda _: {})
    monkeypatch.setattr(fitbit_service, "fetch_steps", lambda d: STEPS_ROLLUP)
    monkeypatch.setattr(fitbit_service, "fetch_active_minutes", lambda d: ACTIVE_MINUTES_ROLLUP)
    monkeypatch.setattr(fitbit_service, "fetch_oxygen_saturation", lambda d: SPO2_DAILY)
    monkeypatch.setattr(fitbit_service, "fetch_weight", lambda d: WEIGHT_SAMPLES)

    data = fitbit_service.build_snapshot_data(date(2026, 9, 17))

    assert data["steps"] == 5305
    assert data["active_minutes"] == 187
    assert data["spo2"] == 97.1
    assert data["weight_kg"] == 81.55
    assert data["resting_heart_rate"] == 60
    assert data["breathing_rate"] == 15.5


def test_build_snapshot_data_survives_one_failing_metric(monkeypatch):
    # A flaky new endpoint must not abort the whole snapshot (which carries the
    # critical sleep/HR data) — the metric just comes back None.
    monkeypatch.setattr(fitbit_service, "fetch_resting_heart_rate",
                        lambda d: {"dataPoints": [{"dailyRestingHeartRate": {"beatsPerMinute": 58}}]})
    monkeypatch.setattr(fitbit_service, "fetch_breathing_rate", lambda d: {"dataPoints": []})
    monkeypatch.setattr(fitbit_service, "fetch_sleep", lambda d: {})
    monkeypatch.setattr(fitbit_service.sleep_score_service, "calculate_sleep_score", lambda _: {})

    def boom(_d):
        raise RuntimeError("Steam-style 500")

    monkeypatch.setattr(fitbit_service, "fetch_steps", boom)
    monkeypatch.setattr(fitbit_service, "fetch_active_minutes", lambda d: ACTIVE_MINUTES_ROLLUP)
    monkeypatch.setattr(fitbit_service, "fetch_oxygen_saturation", lambda d: SPO2_DAILY)
    monkeypatch.setattr(fitbit_service, "fetch_weight", lambda d: WEIGHT_SAMPLES)

    data = fitbit_service.build_snapshot_data(date(2026, 9, 17))

    assert data["steps"] is None  # failed, swallowed
    assert data["active_minutes"] == 187  # others still populated
    assert data["resting_heart_rate"] == 58
