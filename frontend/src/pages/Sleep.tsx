// Sleep tab — the flagship detail view. A per-night breakdown (score, sleep
// window, stage composition) with a night picker, plus duration/score/stage
// trends. All from stored snapshots (getSnapshotHistory) — no live Google
// calls per selection, so browsing nights stays instant.

import { useEffect, useMemo, useState } from 'react'
import { getSnapshotHistory } from '../api/client'
import type { HealthSnapshot } from '../api/types'
import { MetricRing } from '../components/MetricRing'
import { StageBar } from '../components/StageBar'
import { LineTrend } from '../components/charts/LineTrend'
import { StageTrend, type StageDatum } from '../components/charts/StageTrend'
import { Card } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'
import { clockTime, formatDuration, monthDay, relativeDay } from '../lib/format'
import { metricColors } from '../lib/colors'

function hasSleep(s: HealthSnapshot): boolean {
  return s.sleep_duration_minutes != null || s.sleep_score != null
}

export function Sleep() {
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [loading, setLoading] = useState(true)
  // Index into `nights`, or null to track the latest as new data arrives.
  const [selected, setSelected] = useState<number | null>(null)

  useEffect(() => {
    getSnapshotHistory(30)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  // Oldest → newest, only nights that actually have sleep data.
  const nights = useMemo(() => history.filter(hasSleep), [history])

  // Default to the most recent night; clamp if the list shrinks.
  const index = selected == null ? nights.length - 1 : Math.min(selected, nights.length - 1)
  const night = nights[index]

  const stageData: StageDatum[] = useMemo(
    () =>
      nights.slice(-14).map((s) => ({
        label: s.date,
        deep: s.deep_minutes,
        light: s.light_minutes,
        rem: s.rem_minutes,
        awake: s.awake_minutes,
      })),
    [nights],
  )

  if (loading) {
    return (
      <>
        <PageHeader title="Sleep" subtitle="Stages, duration, and score over time" />
        <p className="text-sm text-muted">Loading…</p>
      </>
    )
  }

  if (!night) {
    return (
      <>
        <PageHeader title="Sleep" subtitle="Stages, duration, and score over time" />
        <ComingSoon title="No sleep data yet" note="Once a night syncs from Google Health it’ll show up here." />
      </>
    )
  }

  const window =
    night.sleep_start && night.sleep_end
      ? `${clockTime(night.sleep_start)} – ${clockTime(night.sleep_end)}`
      : null

  return (
    <>
      <PageHeader title="Sleep" subtitle="Stages, duration, and score over time" />

      {/* Selected night */}
      <Card
        title={relativeDay(night.date)}
        subtitle={window ?? undefined}
        action={
          <div className="flex items-center gap-1">
            <NavButton
              label="Previous night"
              disabled={index <= 0}
              onClick={() => setSelected(Math.max(0, index - 1))}
              dir="prev"
            />
            <NavButton
              label="Next night"
              disabled={index >= nights.length - 1}
              onClick={() => setSelected(Math.min(nights.length - 1, index + 1))}
              dir="next"
            />
          </div>
        }
      >
        <div className="flex flex-col gap-8 sm:flex-row sm:items-center">
          <div className="flex shrink-0 items-center gap-6">
            <MetricRing label="Sleep score" value={night.sleep_score} max={100} color={metricColors.sleep} />
            <MetricRing
              label="Time asleep"
              value={night.sleep_duration_minutes}
              max={480 /* 8h goal */}
              display={night.sleep_duration_minutes != null ? formatDuration(night.sleep_duration_minutes) : undefined}
              color={metricColors.duration}
            />
          </div>
          <div className="min-w-0 flex-1">
            <StageBar
              deep={night.deep_minutes}
              light={night.light_minutes}
              rem={night.rem_minutes}
              awake={night.awake_minutes}
            />
            <p className="mt-3 text-[11px] text-faint">
              Proportional stage composition — Google reports per-stage totals, not a segment timeline.
            </p>
          </div>
        </div>
      </Card>

      <Section title="Trends">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card title="Time asleep (30d)">
            <LineTrend
              color={metricColors.duration}
              yAllowDecimals={false}
              points={nights.map((s) => ({
                label: s.date,
                value: s.sleep_duration_minutes != null ? s.sleep_duration_minutes / 60 : null,
              }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(h) => formatDuration(h * 60)}
            />
          </Card>
          <Card title="Sleep score (30d)">
            <LineTrend
              color={metricColors.sleep}
              points={nights.map((s) => ({ label: s.date, value: s.sleep_score }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => Math.round(v)}
            />
          </Card>
        </div>
        <div className="mt-5">
          <Card title="Stage composition (14 nights)">
            <StageTrend data={stageData} labelFormatter={(v) => monthDay(String(v))} />
          </Card>
        </div>
      </Section>
    </>
  )
}

function NavButton({
  label,
  disabled,
  onClick,
  dir,
}: {
  label: string
  disabled: boolean
  onClick: () => void
  dir: 'prev' | 'next'
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="rounded-md p-1.5 text-muted transition-colors hover:bg-elevated hover:text-content disabled:opacity-30 disabled:hover:bg-transparent"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="size-4">
        <path d={dir === 'prev' ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  )
}
