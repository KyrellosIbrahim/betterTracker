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
} as const

export type MetricKey = keyof typeof metricColors
