// Shared formatting helpers, lifted from the original single-file App so every
// page/tab formats dates and durations the same way.
//
// The backend sends naive local datetimes; a date-time string without an offset
// is parsed as local, which is exactly what these rely on.

// "just now" / "12 min ago" / "3h ago" / "2d ago".
export function relativeTime(isoDateTime: string): string {
  const seconds = (Date.now() - new Date(isoDateTime).getTime()) / 1000
  if (seconds < 90) return 'just now'

  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`

  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.round(hours / 24)}d ago`
}

// Minutes as clock time: 384 -> "6:24". Rounding to whole minutes before
// splitting avoids a "6:60" from something like 383.7.
export function formatDuration(minutes: number): string {
  const total = Math.round(minutes)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

// "Today" / "Yesterday" / "Mon, Aug 17". The snapshot shown isn't always
// today's — before that night's sleep syncs, the newest row is yesterday's —
// so headings name the day the data actually belongs to.
export function relativeDay(isoDate: string): string {
  // Append a time so it parses as LOCAL midnight; a bare "2026-08-22" is parsed
  // as UTC and would render as the previous day west of Greenwich.
  const day = new Date(`${isoDate}T00:00:00`)
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const daysAgo = Math.round((today.getTime() - day.getTime()) / 86_400_000)
  if (daysAgo === 0) return 'Today'
  if (daysAgo === 1) return 'Yesterday'
  return day.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

// Short weekday for week-bar axes: "2026-08-22" -> "Fri".
export function weekdayShort(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short' })
}

// Compact month/day for trend axes: "2026-08-22" -> "Aug 22".
export function monthDay(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
