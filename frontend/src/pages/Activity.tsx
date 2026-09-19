// Activity tab — steps and active minutes, now that the backend collects them
// (Phase 4). Weekly step bars plus 30-day trends, from stored snapshots.

import { useEffect, useState } from 'react'
import { getSnapshotHistory } from '../api/client'
import type { HealthSnapshot } from '../api/types'
import { BarWeek } from '../components/charts/BarWeek'
import { LineTrend } from '../components/charts/LineTrend'
import { Card, Stat } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'
import { compactNum, monthDay, weekdayShort } from '../lib/format'
import { latestOf, mean } from '../lib/stats'
import { metricColors } from '../lib/colors'

export function Activity() {
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSnapshotHistory(30)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <>
        <PageHeader title="Activity" subtitle="Steps, active minutes, and workouts" />
        <p className="text-sm text-muted">Loading…</p>
      </>
    )
  }

  const hasAny = history.some((s) => s.steps != null || s.active_minutes != null)
  if (!hasAny) {
    return (
      <>
        <PageHeader title="Activity" subtitle="Steps, active minutes, and workouts" />
        <ComingSoon
          title="No activity data yet"
          note="Steps and active minutes populate as days sync. Older days may need a backfill run to fill in."
        />
      </>
    )
  }

  const last7 = history.slice(-7)
  const stepsLatest = latestOf(history, (s) => s.steps)
  const stepsAvg = mean(last7.map((s) => s.steps))
  const activeLatest = latestOf(history, (s) => s.active_minutes)
  const round = (v: number | null) => (v == null ? null : Math.round(v))

  return (
    <>
      <PageHeader title="Activity" subtitle="Steps, active minutes, and workouts" />

      <Card>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3">
          <Stat label="Steps today" value={stepsLatest?.toLocaleString() ?? '–'} color={metricColors.steps} />
          <Stat label="7-day avg steps" value={round(stepsAvg)?.toLocaleString() ?? '–'} />
          <Stat label="Active minutes" value={activeLatest ?? '–'} unit="min" color={metricColors.breathing} />
        </div>
      </Card>

      <Section title="This week">
        <Card title="Steps">
          <BarWeek
            color={metricColors.steps}
            points={last7.map((s) => ({ label: s.date, value: s.steps }))}
            labelFormatter={(v) => weekdayShort(String(v))}
            valueFormatter={(v) => v.toLocaleString()}
            yTickFormatter={compactNum}
          />
        </Card>
      </Section>

      <Section title="Trends">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card title="Steps (30d)">
            <LineTrend
              color={metricColors.steps}
              points={history.map((s) => ({ label: s.date, value: s.steps }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => v.toLocaleString()}
              yTickFormatter={compactNum}
            />
          </Card>
          <Card title="Active minutes (30d)">
            <LineTrend
              color={metricColors.breathing}
              unit="min"
              points={history.map((s) => ({ label: s.date, value: s.active_minutes }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => Math.round(v)}
            />
          </Card>
        </div>
      </Section>
    </>
  )
}
