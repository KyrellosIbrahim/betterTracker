// Persistent left navigation, grouped like the reference dashboard:
//   Overview  → Dashboard
//   Tracking  → Activity, Sleep, Recovery, Health, Weight, Games
//
// Icons are inline (Lucide-style) SVGs so there's no icon-library dependency.

import { NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'

function Icon({ path }: { path: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="size-[18px] shrink-0"
      aria-hidden
    >
      {path}
    </svg>
  )
}

// Minimal glyphs — enough to read at a glance, not a full icon set.
const icons = {
  dashboard: <><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>,
  activity: <path d="M3 12h4l3 8 4-16 3 8h4" />,
  sleep: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />,
  recovery: <path d="M20.8 5.6a5.5 5.5 0 0 0-8.8 1.4A5.5 5.5 0 0 0 3.2 5.6C1 7.8 1.2 11 4 14l8 7 8-7c2.8-3 3-6.2.8-8.4Z" />,
  health: <path d="M3 12h4l2-5 4 12 2-7h6" />,
  weight: <><circle cx="12" cy="8" r="1.5" /><path d="M6.5 21 9 10h6l2.5 11z" /><path d="M4 21h16" /></>,
  games: <><rect x="2" y="7" width="20" height="12" rx="4" /><path d="M7 12h3M8.5 10.5v3" /><circle cx="16" cy="11" r="1" /><circle cx="18.5" cy="14" r="1" /></>,
} as const

interface NavItem {
  to: string
  label: string
  icon: keyof typeof icons
}

const groups: { heading: string; items: NavItem[] }[] = [
  {
    heading: 'Overview',
    items: [{ to: '/', label: 'Dashboard', icon: 'dashboard' }],
  },
  {
    heading: 'Tracking',
    items: [
      { to: '/activity', label: 'Activity', icon: 'activity' },
      { to: '/sleep', label: 'Sleep', icon: 'sleep' },
      { to: '/recovery', label: 'Recovery', icon: 'recovery' },
      { to: '/health', label: 'Health', icon: 'health' },
      { to: '/weight', label: 'Weight', icon: 'weight' },
      { to: '/games', label: 'Games', icon: 'games' },
    ],
  },
]

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="flex h-full w-60 flex-col gap-6 border-r border-line bg-surface/60 px-3 py-5 backdrop-blur-sm">
      <div className="px-2">
        <span className="bg-gradient-to-r from-accent to-accent-2 bg-clip-text text-xl font-semibold text-transparent">
          BetterTracker
        </span>
      </div>

      <div className="flex flex-col gap-5">
        {groups.map((group) => (
          <div key={group.heading} className="flex flex-col gap-1">
            <span className="px-3 pb-1 text-[11px] font-medium tracking-wider text-faint uppercase">
              {group.heading}
            </span>
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-elevated font-medium text-content'
                      : 'text-muted hover:bg-elevated/60 hover:text-content'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <span className={isActive ? 'text-accent' : ''}>
                      <Icon path={icons[item.icon]} />
                    </span>
                    {item.label}
                  </>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </div>
    </nav>
  )
}
