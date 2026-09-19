// "Updated 3 min ago ↻" — data freshness + a manual refetch button.
// Lifted from the original App; sits next to the data it describes.

import { relativeTime } from '../lib/format'

export function FreshnessAction({
  syncedAt,
  refreshing,
  onRefresh,
}: {
  syncedAt: string | null | undefined
  refreshing: boolean
  onRefresh: () => void
}) {
  return (
    <div className="flex items-center gap-3 text-[13px] text-muted">
      {syncedAt && <span title={new Date(syncedAt).toLocaleString()}>Updated {relativeTime(syncedAt)}</span>}
      <button
        type="button"
        onClick={onRefresh}
        disabled={refreshing}
        aria-label="Refresh health data"
        title="Refetch from Google Health now"
        className="rounded-md px-1.5 py-0.5 text-muted transition-colors hover:bg-elevated hover:text-content disabled:opacity-50"
      >
        <span className={`inline-block ${refreshing ? 'animate-spin' : ''}`}>↻</span>
      </button>
    </div>
  )
}
