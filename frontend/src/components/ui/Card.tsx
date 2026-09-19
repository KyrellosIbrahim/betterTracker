// The one surface primitive every tab builds on. Rounded dark panel with an
// optional titled header + right-aligned action slot. Generalizes the repeated
// card/section markup that used to be inline in App.tsx.

import type { ReactNode } from 'react'

export function Card({
  title,
  subtitle,
  action,
  children,
  className = '',
  padding = true,
}: {
  title?: ReactNode
  subtitle?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
  /** Turn off to lay out edge-to-edge content (e.g. a full-bleed chart). */
  padding?: boolean
}) {
  return (
    <div
      className={`rounded-2xl border border-line bg-surface/80 shadow-sm backdrop-blur-sm ${className}`}
    >
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 px-5 pt-4">
          <div>
            {title && <h3 className="text-sm font-medium text-content">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-[13px] text-muted">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className={padding ? 'p-5' : ''}>{children}</div>
    </div>
  )
}

// Big-number stat, the building block of a KPI row. Value color follows the
// metric so a number reads the same as its chart.
export function Stat({
  label,
  value,
  unit,
  color = 'var(--color-content)',
  hint,
}: {
  label: string
  value: ReactNode
  unit?: string
  color?: string
  hint?: string
}) {
  return (
    <div className="flex flex-col gap-0.5" title={hint}>
      <span className="text-[28px] leading-none font-semibold" style={{ color }}>
        {value ?? '–'}
        {value != null && unit ? (
          <small className="ml-1 text-[13px] font-normal text-muted">{unit}</small>
        ) : null}
      </span>
      <span className="text-[13px] text-muted">{label}</span>
    </div>
  )
}
