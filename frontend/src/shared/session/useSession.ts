import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect, useRef } from "react"

import { apiRequest, setProvenTenantId } from "../api/client"
import { ApiRequestError } from "../api/errors"
import type { Profile } from "./profile"
import { sessionQueryKey } from "./queryClient"

export function useSession() {
  const queryClient = useQueryClient()
  const previousTenant = useRef<string | null | undefined>(undefined)
  const query = useQuery({
    queryKey: sessionQueryKey,
    retry: (count, error) => error instanceof ApiRequestError && error.status >= 500 && count < 1,
    retryDelay: 0,
    queryFn: async () => {
      try {
        return await apiRequest<Profile>("/api/v1/auth/me")
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          setProvenTenantId(null)
          queryClient.removeQueries({
            predicate: (item) => item.queryKey[0] !== sessionQueryKey[0],
          })
          return null
        }
        throw error
      }
    },
  })

  const tenantId = query.data?.tenant?.id ?? null
  useEffect(() => {
    if (!query.isSuccess) return
    if (previousTenant.current !== undefined && previousTenant.current !== tenantId) {
      queryClient.removeQueries({
        predicate: (item) => item.queryKey[0] !== sessionQueryKey[0],
      })
    }
    previousTenant.current = tenantId
    setProvenTenantId(query.data ? tenantId : null)
  }, [query.isSuccess, query.data, tenantId, queryClient])

  return query
}
