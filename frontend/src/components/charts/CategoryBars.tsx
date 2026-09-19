// Categorical comparison bars — the workhorse for the gaming-vs-recovery cards
// (competitive vs casual, active vs sedentary, playtime buckets, …). Carries
// over ComparisonCard's guardrails: a bucket below the sample-size floor is
// dimmed, and the tooltip shows the day count + min/max spread so two bars that
// differ by a hair don't read as a finding when their ranges overlap.

import { Bar, BarChart, Cell, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ReactNode } from 'react'
import { axisTick, chartChrome, chartMargin } from './chartTheme'
import { metricColors } from '../../lib/colors'

const MIN_SAMPLE_DAYS = 5

export interface CategoryDatum {
  label: string
  value: number | null
  sampleDays: number
  spread?: [number | null, number | null]
}

interface CategoryTooltipProps {
  active?: boolean
  payload?: Array<{ payload: CategoryDatum }>
  unit?: string
  valueFormatter?: (v: number) => ReactNode
}

function CategoryTooltip({ active, payload, unit, valueFormatter }: CategoryTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  const d = payload[0].payload
  const [min, max] = d.spread ?? [null, null]
  const thin = d.sampleDays < MIN_SAMPLE_DAYS
  return (
    <div className="rounded-lg border border-line bg-elevated px-3 py-2 text-xs shadow-lg">
      <div className="mb-0.5 text-faint">{d.label}</div>
      <div className="font-medium text-content">
        {d.value == null ? '–' : valueFormatter ? valueFormatter(d.value) : d.value}
        {d.value != null && unit ? <span className="ml-1 font-normal text-muted">{unit}</span> : null}
      </div>
      <div className="mt-1 text-[11px] text-faint">
        {d.sampleDays} day{d.sampleDays === 1 ? '' : 's'}
        {min != null && max != null ? ` · range ${min}–${max}` : ''}
        {thin ? ' · thin' : ''}
      </div>
    </div>
  )
}

export function CategoryBars({
  data,
  color = metricColors.sleep,
  unit,
  valueFormatter,
  yTickFormatter,
  height = 200,
  emptyMessage = 'No data yet.',
}: {
  data: CategoryDatum[]
  color?: string
  unit?: string
  valueFormatter?: (v: number) => ReactNode
  yTickFormatter?: (v: number) => string
  height?: number
  emptyMessage?: string
}) {
  if (!data.some((d) => d.value != null)) {
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
        <XAxis dataKey="label" tick={axisTick} axisLine={{ stroke: chartChrome.grid }} tickLine={false} />
        <YAxis tick={axisTick} axisLine={false} tickLine={false} width={44} tickFormatter={yTickFormatter} />
        <Tooltip
          cursor={{ fill: chartChrome.cursor }}
          content={<CategoryTooltip unit={unit} valueFormatter={valueFormatter} />}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={64}>
          {data.map((d) => (
            // Dim buckets below the sample-size floor — they're not trustworthy.
            <Cell key={d.label} fill={color} fillOpacity={d.sampleDays < MIN_SAMPLE_DAYS ? 0.35 : 1} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
