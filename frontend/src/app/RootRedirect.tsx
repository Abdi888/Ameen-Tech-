import { Navigate } from "react-router"

import { defaultAppPath } from "../shared/navigation/items"
import { useSession } from "../shared/session/useSession"

export function RootRedirect() {
  const session = useSession()
  const profile = session.data
  if (!profile) return null
  if (!profile.tenant) {
    if (profile.memberships.length === 0) return <Navigate to="/platform" replace />
    return <Navigate to="/app" replace />
  }
  return <Navigate to={defaultAppPath(profile.permissions)} replace />
}
