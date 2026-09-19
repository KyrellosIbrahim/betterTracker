// Per-metric colors as plain hex, for components that set SVG presentation
// attributes (MetricRing's `stroke`, Recharts' `fill`/`stroke`) where a
// `var(--token)` value would NOT resolve.
//
// These MIRROR the --color-* tokens in index.css — keep the two in sync. Use
// the CSS tokens for Tailwind utilities (bg-*, text-*), this map for SVG.

export const metricColors = {
  sleep: '#7c5cff',
  duration: '#4fc3f7',
  hr: '#ff6b81',
  breathing: '#4ade80',
  steps: '#f5a623',
  weight: '#38bdf8',
  spo2: '#2dd4bf',
} as const

export type MetricKey = keyof typeof metricColors

// Sleep-stage palette, deepest→lightest, with awake set apart. Reused by the
// per-night stage bar and the stage-composition trend so a stage reads the same
// in both.
export const stageColors = {
  deep: '#4338ca', // indigo
  rem: '#7c5cff', // violet
  light: '#4fc3f7', // cyan
  awake: '#64647c', // faint gray — time out of sleep
} as const

export type SleepStage = keyof typeof stageColors
