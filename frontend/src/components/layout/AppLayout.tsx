// The app frame: persistent sidebar + a top bar + the routed page in <Outlet>.
// The sidebar is fixed on desktop and a slide-in drawer on narrow screens.
//
// App-level context (Google connection, what's playing right now) is fetched
// here so it shows on every page; each page fetches its own domain data.

import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { AuthIndicator } from '../AuthIndicator'
import { getActiveSession, getAuthStatus } from '../../api/client'
import type { ActiveSession, AuthStatus } from '../../api/types'

export function AppLayout() {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null)
  const [nowPlaying, setNowPlaying] = useState<ActiveSession | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  useEffect(() => {
    const load = () => {
      getAuthStatus().then(setAuthStatus).catch(console.error)
      getActiveSession().then(setNowPlaying).catch(console.error)
    }
    load()
    const onVisible = () => {
      if (document.visibilityState === 'visible') load()
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => document.removeEventListener('visibilitychange', onVisible)
  }, [])

  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen md:block">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 left-0 h-full">
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-line bg-bg/70 px-5 py-3 backdrop-blur-md">
          <button
            type="button"
            aria-label="Open navigation"
            onClick={() => setDrawerOpen(true)}
            className="rounded-md p-1.5 text-muted hover:bg-elevated hover:text-content md:hidden"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="size-5">
              <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
            </svg>
          </button>

          <div className="ml-auto flex items-center gap-4">
            {nowPlaying && (
              <span className="inline-flex items-center gap-1.5 text-sm text-accent">
                <span className="size-1.5 animate-pulse rounded-full bg-accent" />
                {nowPlaying.game_name}
              </span>
            )}
            <AuthIndicator status={authStatus} />
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
