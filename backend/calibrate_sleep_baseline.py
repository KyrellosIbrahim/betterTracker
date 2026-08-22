# Derive personalized sleep score anchors from your own sleep history and
# store them in the sleep_baseline table.
#
# Google's algorithm "compares your sleep data against targets tailored to
# your age, gender, and total time you were sleeping" — this is the local
# equivalent: each sub-metric's 10th/90th percentile over a baseline window
# becomes the low/high anchor the score is graded against.
#
# Re-run this occasionally (e.g. every few months) as your sleep changes.
# Existing snapshot scores are NOT rewritten automatically — pass --rescore
# to recompute stored scores with the new baseline so trends stay comparable.
#
# Run from backend/:
#   venv/bin/python calibrate_sleep_baseline.py --start 2026-06-12 --rescore

import argparse
import statistics as st
import time
from datetime import date, datetime, timedelta

from database import SessionLocal
from models.health_snapshot import HealthSnapshot
from models.sleep_baseline import SleepBaseline
from services import fitbit_service, sleep_score_service

MIN_SAMPLE_DAYS = 14
REQUEST_DELAY_SECONDS = 0.2


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def collect_metrics(start: date, end: date) -> list[dict]:
    """Fetch raw sleep for each day in the range and extract per-night metrics."""
    metrics = []
    for offset in range((end - start).days + 1):
        target = start + timedelta(days=offset)
        try:
            data = fitbit_service.fetch_sleep(target)
        except Exception as exc:
            print(f"{target}  skipped ({type(exc).__name__}: {exc})")
            continue
        night = sleep_score_service.extract_metrics(data)
        if night:
            metrics.append(night)
        time.sleep(REQUEST_DELAY_SECONDS)
    return metrics


def save_baseline(anchors: dict, sample_days: int, db) -> SleepBaseline:
    """Upsert the single baseline row."""
    row = db.query(SleepBaseline).first() or SleepBaseline(id=1)
    row.duration_low, row.duration_high = anchors["duration_minutes"]
    row.deep_pct_low, row.deep_pct_high = anchors["deep_pct"]
    row.rem_pct_low, row.rem_pct_high = anchors["rem_pct"]
    row.awake_low, row.awake_high = anchors["awake_minutes"]
    row.sample_days = sample_days
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def rescore_snapshots(db) -> int:
    """Recompute stored sleep scores using the current baseline."""
    updated = 0
    for snap in db.query(HealthSnapshot).filter(HealthSnapshot.sleep_duration_minutes.isnot(None)).all():
        result = sleep_score_service.score_metrics({
            "minutes_asleep": snap.sleep_duration_minutes,
            "deep_minutes": snap.deep_minutes or 0,
            "light_minutes": snap.light_minutes or 0,
            "rem_minutes": snap.rem_minutes or 0,
            "awake_minutes": snap.awake_minutes or 0,
            "has_stages": bool(snap.deep_minutes or snap.rem_minutes),
        })
        snap.sleep_score = result["score"]
        updated += 1
    db.commit()
    return updated


def describe(scores: list[int], label: str) -> None:
    if not scores:
        return
    bands = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    for s in scores:
        bands[sleep_score_service._rating(s)] += 1
    print(
        f"{label}: mean={st.mean(scores):.1f} median={st.median(scores):.0f} "
        f"sd={st.pstdev(scores):.1f} range={min(scores)}-{max(scores)}"
    )
    print("   " + "  ".join(f"{name} {count}" for name, count in bands.items()))


def main():
    parser = argparse.ArgumentParser(description="Calibrate the sleep score to your own baseline.")
    parser.add_argument("--start", type=parse_date, required=True, help="First day of the baseline window")
    parser.add_argument("--end", type=parse_date, default=date.today(), help="Last day, inclusive (default: today)")
    parser.add_argument("--rescore", action="store_true", help="Recompute stored snapshot scores afterwards")
    args = parser.parse_args()

    if args.start > args.end:
        parser.error("--start must be on or before --end")

    print(f"Collecting sleep metrics {args.start} → {args.end} ...")
    metrics = collect_metrics(args.start, args.end)
    if len(metrics) < MIN_SAMPLE_DAYS:
        raise SystemExit(
            f"Only {len(metrics)} usable nights found; need at least {MIN_SAMPLE_DAYS} "
            "for a meaningful baseline. Widen the date range."
        )

    db = SessionLocal()
    try:
        before = [s.sleep_score for s in db.query(HealthSnapshot).all() if s.sleep_score is not None]

        anchors = sleep_score_service.derive_anchors(metrics)
        save_baseline(anchors, len(metrics), db)
        sleep_score_service.clear_anchor_cache()

        print(f"\nBaseline from {len(metrics)} nights (anchors are personal p10 / p90, clamped):")
        for name, (low, high) in anchors.items():
            print(f"  {name:18} {low:>7.3f}  →  {high:>7.3f}")

        if args.rescore:
            updated = rescore_snapshots(db)
            after = [s.sleep_score for s in db.query(HealthSnapshot).all() if s.sleep_score is not None]
            print(f"\nRescored {updated} stored snapshots.")
            describe(before, "before")
            describe(after, "after ")
        else:
            print("\nBaseline saved. Re-run with --rescore to update stored snapshot scores.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
