// Recovery tab — the two "how rested is my body" signals: resting heart rate
// and breathing rate, with sleep score alongside since it moves with them.
// All from stored snapshots.

import { useEffect, useState } from 'react'
import { getSnapshotHistory } from '../api/client'
import type { HealthSnapshot } from '../api/types'
import { LineTrend } from '../components/charts/LineTrend'
import { Card, Stat } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'
import { monthDay } from '../lib/format'
import { latestOf, mean } from '../lib/stats'
import { metricColors } from '../lib/colors'

export function Recovery() {
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
        <PageHeader title="Recovery" subtitle="Resting heart rate and breathing rate" />
        <p className="text-sm text-muted">Loading…</p>
      </>
    )
  }

  const hasAny = history.some((s) => s.resting_heart_rate != null || s.breathing_rate != null)
  if (!hasAny) {
    return (
      <>
        <PageHeader title="Recovery" subtitle="Resting heart rate and breathing rate" />
        <ComingSoon title="No recovery data yet" note="Resting HR and breathing rate show up once a day syncs from Google Health." />
      </>
    )
  }

  const last7 = history.slice(-7)
  const restingLatest = latestOf(history, (s) => s.resting_heart_rate)
  const restingAvg = mean(last7.map((s) => s.resting_heart_rate))
  const breathingLatest = latestOf(history, (s) => s.breathing_rate)
  const breathingAvg = mean(last7.map((s) => s.breathing_rate))
  const spo2Latest = latestOf(history, (s) => s.spo2)

  const round = (v: number | null, d = 0) => (v == null ? null : Number(v.toFixed(d)))

  return (
    <>
      <PageHeader title="Recovery" subtitle="Resting heart rate and breathing rate" />

      <Card>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5">
          <Stat label="Resting HR" value={restingLatest ?? '–'} unit="bpm" color={metricColors.hr} />
          <Stat label="7-day avg HR" value={round(restingAvg) ?? '–'} unit="bpm" />
          <Stat label="Breathing" value={round(breathingLatest, 1) ?? '–'} unit="/min" color={metricColors.breathing} />
          <Stat label="7-day avg breathing" value={round(breathingAvg, 1) ?? '–'} unit="/min" />
          <Stat label="SpO₂" value={round(spo2Latest, 1) ?? '–'} unit="%" color={metricColors.spo2} />
        </div>
      </Card>

      <Section title="Trends">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card title="Resting heart rate (30d)">
            <LineTrend
              color={metricColors.hr}
              unit="bpm"
              points={history.map((s) => ({ label: s.date, value: s.resting_heart_rate }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => Math.round(v)}
            />
          </Card>
          <Card title="Breathing rate (30d)">
            <LineTrend
              color={metricColors.breathing}
              unit="/min"
              points={history.map((s) => ({ label: s.date, value: s.breathing_rate }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => v.toFixed(1)}
            />
          </Card>
          <Card title="Blood oxygen (30d)">
            <LineTrend
              color={metricColors.spo2}
              unit="%"
              points={history.map((s) => ({ label: s.date, value: s.spo2 }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => v.toFixed(1)}
            />
          </Card>
        </div>
      </Section>
    </>
  )
}
