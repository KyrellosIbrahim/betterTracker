// Tiny numeric helpers for the overview tabs. Nulls are ignored, not treated
// as zero — a missing day shouldn't drag an average down.

export function mean(values: Array<number | null | undefined>): number | null {
  const nums = values.filter((v): v is number => v != null)
  if (nums.length === 0) return null
  return nums.reduce((a, b) => a + b, 0) / nums.length
}

// Most recent non-null value from a chronological (oldest→newest) list.
export function latestOf<T>(items: T[], pick: (item: T) => number | null | undefined): number | null {
  for (let i = items.length - 1; i >= 0; i--) {
    const v = pick(items[i])
    if (v != null) return v
  }
  return null
}
