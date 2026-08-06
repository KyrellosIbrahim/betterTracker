# Backfill historical health snapshots from the Google Health API.
# Google Health already holds weeks of sleep/HR history, so this fills the
# trend charts and insights immediately instead of waiting for daily snapshots
# to accumulate.
#
# Requires a stored Google token (visit /auth/google/login once first).
# Days already in the DB are skipped unless --force is passed, so re-running
# after a partial failure is safe.
#
# Run from backend/:
#   venv/bin/python backfill_health.py --start 2026-06-12
#   venv/bin/python backfill_health.py --start 2026-06-12 --end 2026-08-04 --force

import argparse
import time
from datetime import date, datetime, timedelta

from database import SessionLocal
from models.health_snapshot import HealthSnapshot
from services import fitbit_service

# Pause between days so a long backfill doesn't hammer the API.
REQUEST_DELAY_SECONDS = 0.3


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def summarize(data: dict) -> str:
    """One-line summary of a day's fetched metrics."""
    score = data.get("sleep_score")
    duration = data.get("sleep_duration_minutes")
    hours = f"{duration / 60:.1f}h" if duration else "–"
    return (
        f"score={score if score is not None else '–':>4}  "
        f"sleep={hours:>5}  "
        f"rhr={data.get('resting_heart_rate') or '–':>4}  "
        f"br={data.get('breathing_rate') or '–'}"
    )


def main():
    parser = argparse.ArgumentParser(description="Backfill daily health snapshots.")
    parser.add_argument("--start", type=parse_date, required=True, help="First day to fetch (YYYY-MM-DD)")
    parser.add_argument("--end", type=parse_date, default=date.today(), help="Last day, inclusive (default: today)")
    parser.add_argument("--force", action="store_true", help="Refetch days that already have a snapshot")
    args = parser.parse_args()

    if args.start > args.end:
        parser.error("--start must be on or before --end")

    db = SessionLocal()
    existing_dates = {
        row.date for row in db.query(HealthSnapshot.date).filter(HealthSnapshot.date.between(args.start, args.end))
    }

    total_days = (args.end - args.start).days + 1
    print(f"Backfilling {total_days} days: {args.start} → {args.end}")
    if existing_dates and not args.force:
        print(f"{len(existing_dates)} day(s) already stored — skipping (use --force to refetch)\n")

    saved = skipped = empty = failed = 0
    try:
        for offset in range(total_days):
            target = args.start + timedelta(days=offset)

            if target in existing_dates and not args.force:
                skipped += 1
                continue

            try:
                data = fitbit_service.build_snapshot_data(target)
            except Exception as exc:
                # One bad day shouldn't abort the run — log it and keep going.
                print(f"{target}  FAILED  {type(exc).__name__}: {exc}")
                failed += 1
                continue

            if all(value is None for value in data.values()):
                # No wearable data for this day (device not worn, gap in history)
                print(f"{target}  no data")
                empty += 1
            else:
                fitbit_service.save_health_snapshot(target, data, db)
                print(f"{target}  {summarize(data)}")
                saved += 1

            time.sleep(REQUEST_DELAY_SECONDS)
    finally:
        db.close()

    print(f"\nDone. saved={saved} skipped={skipped} no-data={empty} failed={failed}")
    if failed:
        print("Re-run the same command to retry failed days (stored days are skipped).")


if __name__ == "__main__":
    main()
