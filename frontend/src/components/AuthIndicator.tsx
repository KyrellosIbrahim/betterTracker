// Google Health connection state, shown in the app header.
// Lifted verbatim from the original App so every page shares one indicator.

import { GOOGLE_LOGIN_URL } from '../api/client'
import type { AuthStatus } from '../api/types'

// Derive the UI state once, so the booleans don't get scattered through JSX.
// 'unknown' covers the in-flight fetch — rendering nothing beats flashing the
// wrong state on every page load.
export type AuthState = 'unknown' | 'connected' | 'reconnect' | 'disconnected'

export function authState(status: AuthStatus | null): AuthState {
  if (!status) return 'unknown'
  if (status.connected) return 'connected'
  // needs_reauth means the grant died — looks like "not connected" to the user,
  // but it means data silently stopped updating, so it gets different wording.
  return status.needs_reauth ? 'reconnect' : 'disconnected'
}

export function AuthIndicator({ status }: { status: AuthStatus | null }) {
  const state = authState(status)
  if (state === 'unknown') return null

  if (state === 'connected') {
    // Deliberately no timestamp here: this indicator is about the *connection*.
    // Data freshness lives next to the data (see FreshnessAction).
    return (
      <span className="inline-flex items-center gap-1.5 text-sm text-good">
        <span className="size-1.5 rounded-full bg-good" />
        Connected
        {/* Non-fatal failure (e.g. invalid_client) — reconnecting wouldn't fix
            it, so warn rather than prompting. */}
        {status?.last_error && (
          <span className="ml-1 text-warn" title={status.last_error}>
            ⚠
          </span>
        )}
      </span>
    )
  }

  return (
    <a
      href={GOOGLE_LOGIN_URL}
      className="text-sm font-medium text-accent underline-offset-2 hover:underline"
    >
      {state === 'reconnect' ? 'Reconnect Google Health' : 'Connect Google Health'}
    </a>
  )
}
