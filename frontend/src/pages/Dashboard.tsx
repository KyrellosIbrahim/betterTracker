// Overview tab — the migrated original dashboard: today's rings, trend charts,
// and the correlation insight cards. Still uses the original MetricRing /
// TrendChart / ComparisonCard; Phase 2 swaps TrendChart for an interactive
// Recharts version and Phase 3 moves the game-correlation cards to the Games tab.

import { useCallback, useEffect, useState } from 'react'
import {
  getInsightsByCompetitive,
  getLateNightImpact,
  getSnapshot,
  getSnapshotHistory,
  getWindDownImpact,
} from '../api/client'
import type {
  CompetitiveInsight,
  HealthSnapshot,
  LateNightImpact,
  SleepImpactBucket,
  WindDownImpact,
} from '../api/types'
import { MetricRing } from '../components/MetricRing'
import { TrendChart } from '../components/TrendChart'
import { ComparisonCard } from '../components/ComparisonCard'
import { Card } from '../components/ui/Card'
import { PageHeader, Section } from '../components/ui/Section'
import { FreshnessAction } from '../components/FreshnessAction'
import { formatDuration, relativeDay } from '../lib/format'
import { metricColors } from '../lib/colors'

// A row can exist but be empty — asked before that night's sleep reached Google.
function hasData(snapshot: HealthSnapshot | null): boolean {
  return snapshot != null && (snapshot.sleep_score != null || snapshot.resting_heart_rate != null)
}

export function Dashboard() {
  const [today, setToday] = useState<HealthSnapshot | null>(null)
  const [history, setHistory] = useState<HealthSnapshot[]>([])
  const [competitive, setCompetitive] = useState<CompetitiveInsight[]>([])
  const [windDown, setWindDown] = useState<WindDownImpact | null>(null)
  const [lateNight, setLateNight] = useState<LateNightImpact | null>(null)
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
    getWindDownImpact().then(setWindDown).catch(console.error)
    getLateNightImpact().then(setLateNight).catch(console.error)
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

  // Every bucket insight has the same shape, so build its card row the same way.
  const bucketRow = (label: string, bucket: SleepImpactBucket | undefined) => ({
    label,
    value: bucket?.avg_sleep_score,
    sampleDays: bucket?.sample_days,
    spread: [bucket?.sleep_score_min ?? null, bucket?.sleep_score_max ?? null] as [number | null, number | null],
  })

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
          <MetricRing label="Resting HR" value={latest?.resting_heart_rate} max={100} unit=" bpm" color={metricColors.hr} />
          <MetricRing
            label="Breathing"
            value={latest?.breathing_rate ?? null}
            max={30 /* typical resting range tops out ~20/min; headroom so a normal night isn't a full ring */}
            unit=" /min"
            color={metricColors.breathing}
          />
        </div>
      </Card>

      <Section title="Trends">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          <Card>
            <TrendChart
              title="Sleep score (30d)"
              color={metricColors.sleep}
              points={history.map((s) => ({ label: s.date, value: s.sleep_score }))}
            />
          </Card>
          <Card>
            <TrendChart
              title="Resting HR (30d)"
              color={metricColors.hr}
              points={history.map((s) => ({ label: s.date, value: s.resting_heart_rate }))}
            />
          </Card>
        </div>
      </Section>

      <Section title="Gaming vs recovery">
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
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
          <ComparisonCard
            title="Sleep score by wind-down gap (last session → bed)"
            emptyMessage="No sessions with a measurable wind-down gap yet."
            rows={[
              bucketRow('<30 min', windDown?.under_30min),
              bucketRow('30–90 min', windDown?.['30_to_90min']),
              bucketRow('90+ min', windDown?.over_90min),
            ]}
          />
          <ComparisonCard
            title="Sleep score: late-night gaming vs earlier"
            emptyMessage="No sessions recorded yet."
            rows={[
              bucketRow('Late night', lateNight?.late_night_gaming),
              bucketRow('Earlier', lateNight?.earlier_gaming),
              bucketRow('No gaming', lateNight?.no_gaming),
            ]}
          />
        </div>
      </Section>
    </>
  )
}
