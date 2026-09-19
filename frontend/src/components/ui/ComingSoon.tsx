// Placeholder for tabs whose backend data doesn't exist yet (Activity, Weight).
// Kept intentionally plain so it never looks like a real, populated view.

export function ComingSoon({ title, note }: { title: string; note?: string }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-center">
      <div className="grid size-12 place-items-center rounded-2xl border border-line bg-surface text-2xl">
        ⏳
      </div>
      <h2 className="text-lg font-medium text-content">{title}</h2>
      <p className="max-w-sm text-sm text-muted">
        {note ?? 'This section is coming soon — the backend doesn’t collect this data yet.'}
      </p>
    </div>
  )
}
