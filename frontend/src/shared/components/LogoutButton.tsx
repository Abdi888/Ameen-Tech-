import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useNavigate } from "react-router"

import { apiRequest, setProvenTenantId } from "../api/client"

export function LogoutButton() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [pending, setPending] = useState(false)

  async function onClick() {
    setPending(true)
    try {
      await apiRequest("/api/v1/auth/logout", { method: "POST", body: {} })
    } catch {
      // A revoked session still has to leave the workspace.
    } finally {
      setProvenTenantId(null)
      queryClient.clear()
      navigate("/login", { replace: true })
    }
  }

  return (
    <button type="button" className="button button-secondary logout" onClick={onClick} disabled={pending}>
      Log out
    </button>
  )
}
