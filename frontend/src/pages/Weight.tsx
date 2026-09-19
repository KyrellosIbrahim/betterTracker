// Weight tab — body weight over time, now that the backend collects it
// (Phase 4). Readings are sparse (only days with a weigh-in), so the trend
// bridges gaps.

import { useEffect, useState } from 'react'
import { getSnapshotHistory } from '../api/client'
import type { HealthSnapshot } from '../api/types'
import { LineTrend } from '../components/charts/LineTrend'
import { Card, Stat } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'
import { monthDay } from '../lib/format'
import { metricColors } from '../lib/colors'

export function Weight() {
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSnapshotHistory(60)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <>
        <PageHeader title="Weight" subtitle="Body weight over time" />
        <p className="text-sm text-muted">Loading…</p>
      </>
    )
  }

  // Only days with an actual weigh-in.
  const weighed = history.filter((s) => s.weight_kg != null)
  if (weighed.length === 0) {
    return (
      <>
        <PageHeader title="Weight" subtitle="Body weight over time" />
        <ComingSoon
          title="No weight readings yet"
          note="Weigh-ins show up here once they sync. Older readings may need a backfill run to fill in."
        />
      </>
    )
  }

  const latest = weighed.at(-1)!.weight_kg!
  const first = weighed[0].weight_kg!
  const change = latest - first
  const changeStr = `${change >= 0 ? '+' : ''}${change.toFixed(1)}`

  return (
    <>
      <PageHeader title="Weight" subtitle="Body weight over time" />

      <Card>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-3">
          <Stat label="Latest" value={latest.toFixed(1)} unit="kg" color={metricColors.weight} />
          <Stat label={`Change (${weighed.length} readings)`} value={changeStr} unit="kg" />
          <Stat label="First in range" value={first.toFixed(1)} unit="kg" />
        </div>
      </Card>

      <Section title="Trend">
        <Card title="Weight (kg)">
          <LineTrend
            color={metricColors.weight}
            unit="kg"
            height={220}
            points={history.map((s) => ({ label: s.date, value: s.weight_kg }))}
            labelFormatter={(v) => monthDay(String(v))}
            valueFormatter={(v) => v.toFixed(1)}
          />
        </Card>
      </Section>
    </>
  )
}
