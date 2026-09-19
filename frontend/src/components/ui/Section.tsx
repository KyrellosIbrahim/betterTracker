// Page-level headings. `PageHeader` is the big title at the top of a tab;
// `Section` groups related cards under a smaller subheading. Both take an
// optional right-aligned action slot (e.g. a freshness/refresh control).

import type { ReactNode } from 'react'

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: ReactNode
  subtitle?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-content">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

export function Section({
  title,
  action,
  children,
}: {
  title?: ReactNode
  action?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="mt-8 first:mt-0">
      {(title || action) && (
        <div className="mb-3 flex items-baseline justify-between gap-4">
          {title && <h2 className="text-sm font-medium tracking-wide text-muted uppercase">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  )
}
