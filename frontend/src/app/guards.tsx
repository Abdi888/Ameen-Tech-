import { Navigate, Outlet, useLocation } from "react-router"

import { ApiRequestError, unavailableMessage } from "../shared/api/errors"
import { LogoutButton } from "../shared/components/LogoutButton"
import {
  AccessDenied,
  EmptyDestination,
  ErrorStatus,
  FullScreen,
  LoadingStatus,
} from "../shared/components/Status"
import { destinations, permissionSet } from "../shared/navigation/items"
import { useSession } from "../shared/session/useSession"

export function RequireSession() {
  const session = useSession()
  const location = useLocation()

  if (session.isPending) {
    return (
      <FullScreen>
        <LoadingStatus />
      </FullScreen>
    )
  }
  if (session.isError) {
    const message = session.error instanceof ApiRequestError ? session.error.message : unavailableMessage()
    if (session.error instanceof ApiRequestError && session.error.status === 403) {
      return (
        <FullScreen>
          <AccessDenied message={message} />
          <LogoutButton />
        </FullScreen>
      )
    }
    return (
      <FullScreen>
        <ErrorStatus message={message} onRetry={() => void session.refetch()} />
      </FullScreen>
    )
  }
  if (!session.data) {
    const path = location.pathname
    const canReturn = path.startsWith("/app/") || path.startsWith("/platform/")
    const target = canReturn ? `/login?return=${encodeURIComponent(path)}` : "/login"
    return <Navigate to={target} replace />
  }
  return <Outlet />
}

export function TenantGate() {
  const session = useSession()
  const profile = session.data
  if (!profile) return null
  if (!profile.tenant) {
    if (profile.memberships.length === 0) return <Navigate to="/platform" replace />
    return (
      <main className="fullscreen">
        <div className="card status-block">
          <h1>Workspace unavailable</h1>
          <p>This session does not have an active tenant workspace.</p>
          <LogoutButton />
        </div>
      </main>
    )
  }
  return <Outlet />
}

export function Permitted({ path }: { path: string }) {
  const session = useSession()
  const destination = destinations.find((item) => item.path === path)
  const granted = permissionSet(session.data?.permissions ?? [])
  if (!destination || !destination.allow(granted)) return <AccessDenied />
  return <EmptyDestination title={destination.title} />
}

export function UnavailablePage() {
  return <EmptyDestination title="Page not available" />
}
