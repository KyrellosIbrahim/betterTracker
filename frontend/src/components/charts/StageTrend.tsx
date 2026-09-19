// Sleep-stage composition across nights — a stacked bar per night (deep/light/
// rem/awake minutes). Hover shows every stage for that night. Same honesty
// caveat as StageBar: these are per-stage totals, not a segment timeline.

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ReactNode } from 'react'
import { axisTick, chartChrome, chartMargin } from './chartTheme'
import { stageColors, type SleepStage } from '../../lib/colors'
import { formatHm } from '../../lib/format'

export interface StageDatum {
  label: string // ISO date
  deep: number | null
  light: number | null
  rem: number | null
  awake: number | null
}

const ORDER: SleepStage[] = ['deep', 'light', 'rem', 'awake']
const LABELS: Record<SleepStage, string> = { deep: 'Deep', light: 'Light', rem: 'REM', awake: 'Awake' }

interface StageTooltipProps {
  active?: boolean
  payload?: Array<{ dataKey?: string; value?: number | null; color?: string }>
  label?: string | number
  labelFormatter?: (label: string | number) => ReactNode
}

function StageTooltip({ active, payload, label, labelFormatter }: StageTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-lg border border-line bg-elevated px-3 py-2 text-xs shadow-lg">
      {label != null && (
        <div className="mb-1 text-faint">{labelFormatter ? labelFormatter(label) : label}</div>
      )}
      <div className="flex flex-col gap-0.5">
        {payload
          .filter((row) => row.value != null && row.value > 0)
          .map((row) => (
            <div key={row.dataKey} className="flex items-center gap-1.5 text-content">
              <span className="size-2 rounded-full" style={{ backgroundColor: row.color }} />
              <span className="text-muted">{LABELS[row.dataKey as SleepStage] ?? row.dataKey}</span>
              <span className="ml-auto font-medium">{formatHm(row.value as number)}</span>
            </div>
          ))}
      </div>
    </div>
  )
}

export function StageTrend({
  data,
  height = 200,
  labelFormatter,
  emptyMessage = 'No sleep-stage data yet.',
}: {
  data: StageDatum[]
  height?: number
  labelFormatter?: (label: string | number) => ReactNode
  emptyMessage?: string
}) {
  const hasAny = data.some((d) => (d.deep ?? 0) + (d.light ?? 0) + (d.rem ?? 0) + (d.awake ?? 0) > 0)

  if (!hasAny) {
    return (
      <p className="rounded-lg bg-elevated/60 px-4 py-6 text-[13px] text-muted" style={{ minHeight: height }}>
        {emptyMessage}
      </p>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={chartMargin}>
        <CartesianGrid stroke={chartChrome.grid} strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="label"
          tick={axisTick}
          tickFormatter={labelFormatter ? (v) => String(labelFormatter(v)) : undefined}
          axisLine={{ stroke: chartChrome.grid }}
          tickLine={false}
          minTickGap={16}
        />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} width={36} />
        <Tooltip
          cursor={{ fill: chartChrome.cursor }}
          content={<StageTooltip labelFormatter={labelFormatter} />}
        />
        {ORDER.map((stage, i) => (
          <Bar
            key={stage}
            dataKey={stage}
            stackId="stages"
            fill={stageColors[stage]}
            // Round only the top of the topmost non-empty segment; keeping it
            // simple, round the last stage in the stack.
            radius={i === ORDER.length - 1 ? [3, 3, 0, 0] : undefined}
            maxBarSize={40}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
