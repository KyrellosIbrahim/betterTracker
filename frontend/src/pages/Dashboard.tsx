// Overview tab — today's rings, trend charts, and a single gaming-vs-recovery
// teaser (the full set of correlation cards lives on the Games tab). Uses
// MetricRing + the interactive Recharts LineTrend + ComparisonCard.

import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getInsightsByCompetitive, getSnapshot, getSnapshotHistory } from '../api/client'
import type { CompetitiveInsight, HealthSnapshot } from '../api/types'
import { MetricRing } from '../components/MetricRing'
import { LineTrend } from '../components/charts/LineTrend'
import { ComparisonCard } from '../components/ComparisonCard'
import { Card } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { FreshnessAction } from '../components/FreshnessAction'
import { formatDuration, monthDay, relativeDay } from '../lib/format'
import { metricColors } from '../lib/colors'

// A row can exist but be empty — asked before that night's sleep reached Google.
function hasData(snapshot: HealthSnapshot | null): boolean {
  return snapshot != null && (snapshot.sleep_score != null || snapshot.resting_heart_rate != null)
}

export function Dashboard() {
  const [today, setToday] = useState<HealthSnapshot | null>(null)
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [competitive, setCompetitive] = useState<CompetitiveInsight[]>([])
  const [refreshing, setRefreshing] = useState(false)

  const loadAll = useCallback(async (force = false) => {
    // getSnapshot refetches from Google only when the stored row is stale
    // (~3ms otherwise), so it's safe on every load. Awaited before the history
    // call so the chart includes any refresh it just triggered.
    try {
      setToday(await getSnapshot(undefined, force))
    } catch (e) {
      console.error(e)
    }
    getSnapshotHistory(30).then(setHistory).catch(console.error)
    getInsightsByCompetitive().then(setCompetitive).catch(console.error)
  }, [])

  useEffect(() => {
    loadAll()
    const onVisible = () => {
      if (document.visibilityState === 'visible') loadAll()
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [loadAll])

  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      await loadAll(true)
    } finally {
      setRefreshing(false)
    }
  }, [loadAll])

  const competitiveRow = competitive.find((c) => c.is_competitive)
  const casualRow = competitive.find((c) => !c.is_competitive)
  // Prefer today's freshly-synced row; fall back to the newest stored day when
  // today has nothing yet (e.g. loading before sleep has synced).
  const latest = hasData(today) ? today : (history.at(-1) ?? null)
  const sleepMinutes = latest?.sleep_duration_minutes ?? null

  return (
    <>
      <PageHeader
        title={latest ? relativeDay(latest.date) : 'Dashboard'}
        subtitle="Your recovery at a glance"
        action={<FreshnessAction syncedAt={latest?.synced_at} refreshing={refreshing} onRefresh={handleRefresh} />}
      />

      {/* Today's rings */}
      <Card>
        <div className="flex flex-wrap justify-around gap-8">
          <MetricRing label="Sleep score" value={latest?.sleep_score} max={100} color={metricColors.sleep} />
          <MetricRing
            label="Sleep duration"
            value={sleepMinutes}
            max={480 /* 8h goal, in minutes */}
            display={sleepMinutes != null ? formatDuration(sleepMinutes) : undefined}
            color={metricColors.duration}
          />
          {/* Resting HR & breathing are lower-is-better, so the ring is inverted
              (a lower value reads fuller). Anchors are display-only healthy-adult
              bounds: full at the best end, empty at the worst — they don't touch
              stored data or the sleep score. */}
          <MetricRing
            label="Resting HR"
            value={latest?.resting_heart_rate}
            min={50 /* full */}
            max={90 /* empty */}
            invert
            unit=" bpm"
            color={metricColors.hr}
          />
          <MetricRing
            label="Breathing"
            value={latest?.breathing_rate ?? null}
            min={12 /* full */}
            max={22 /* empty */}
            invert
            unit=" /min"
            color={metricColors.breathing}
          />
        </div>
      </Card>

      <Section title="Trends">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card title="Sleep score (30d)">
            <LineTrend
              color={metricColors.sleep}
              points={history.map((s) => ({ label: s.date, value: s.sleep_score }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => Math.round(v)}
            />
          </Card>
          <Card title="Resting HR (30d)">
            <LineTrend
              color={metricColors.hr}
              unit="bpm"
              points={history.map((s) => ({ label: s.date, value: s.resting_heart_rate }))}
              labelFormatter={(v) => monthDay(String(v))}
              valueFormatter={(v) => Math.round(v)}
            />
          </Card>
        </div>
      </Section>

      <Section
        title="Gaming vs recovery"
        action={
          <Link to="/games" className="text-[13px] font-medium text-accent hover:underline">
            See all in Games →
          </Link>
        }
      >
        <ComparisonCard
          title="Avg resting HR: competitive vs casual days"
          emptyMessage="No sessions recorded yet — play something to start comparing."
          rows={[
            {
              label: 'Competitive',
              value: competitiveRow?.avg_resting_hr,
              unit: 'bpm',
              sampleDays: competitiveRow?.recovery_days,
              spread: [competitiveRow?.resting_hr_min ?? null, competitiveRow?.resting_hr_max ?? null],
            },
            {
              label: 'Casual',
              value: casualRow?.avg_resting_hr,
              unit: 'bpm',
              sampleDays: casualRow?.recovery_days,
              spread: [casualRow?.resting_hr_min ?? null, casualRow?.resting_hr_max ?? null],
            },
          ]}
        />
      </Section>
    </>
  )
}
