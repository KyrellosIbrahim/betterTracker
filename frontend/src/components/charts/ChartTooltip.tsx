// Shared hover tooltip for every chart, styled to the design tokens. Recharts
// clones this element and injects `active`/`payload`/`label`; the other props
// come from the chart that renders it.

import type { ReactNode } from 'react'

interface ChartTooltipProps {
  active?: boolean
  payload?: Array<{ value?: number | string | null; name?: string; color?: string }>
  label?: string | number
  unit?: string
  /** Format the header (usually the x value, e.g. an ISO date → "Fri, Aug 22"). */
  labelFormatter?: (label: string | number) => ReactNode
  /** Format the numeric value shown. */
  valueFormatter?: (value: number) => ReactNode
}

export function ChartTooltip({
  active,
  payload,
  label,
  unit,
  labelFormatter,
  valueFormatter,
}: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null

  const raw = payload[0]?.value
  if (raw == null) return null
  const value = typeof raw === 'number' && valueFormatter ? valueFormatter(raw) : raw
  const swatch = payload[0]?.color

  return (
    <div className="rounded-lg border border-line bg-elevated px-3 py-2 text-xs shadow-lg">
      {label != null && (
        <div className="mb-0.5 text-faint">{labelFormatter ? labelFormatter(label) : label}</div>
      )}
      <div className="flex items-center gap-1.5 font-medium text-content">
        {swatch && <span className="size-2 rounded-full" style={{ backgroundColor: swatch }} />}
        {value}
        {unit ? <span className="font-normal text-muted">{unit}</span> : null}
      </div>
    </div>
  )
}
