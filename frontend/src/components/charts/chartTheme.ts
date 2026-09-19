// Chart "chrome" colors — axes, grid, tooltip surface. These MIRROR the
// --color-* tokens in index.css (Recharts sets SVG attributes, where a
// var(--token) value would not resolve — same reason as lib/colors.ts).
// Keep in sync with index.css.

export const chartChrome = {
  grid: '#272738', // --color-line
  axis: '#64647c', // --color-faint
  tick: '#9a9ab2', // --color-muted
  tooltipBg: '#1b1b2b', // --color-elevated
  tooltipBorder: '#272738', // --color-line
  cursor: 'rgba(124, 92, 255, 0.12)', // accent wash behind the hovered point
} as const

// Shared axis defaults so every chart's ticks read the same.
export const axisTick = { fill: chartChrome.tick, fontSize: 11 } as const

// Common margins — enough room for tick labels without wasting space.
export const chartMargin = { top: 8, right: 8, bottom: 0, left: -16 } as const
