import { PageHeader } from '../components/ui/Section'
import { ComingSoon } from '../components/ui/ComingSoon'

export function Health() {
  return (
    <>
      <PageHeader title="Health" subtitle="Everything Google Health reports, in one place" />
      <ComingSoon title="Health overview" note="A cross-metric overview lands in Phase 3 — the data is already collected." />
    </>
  )
}
