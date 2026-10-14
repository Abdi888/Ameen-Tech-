import { QueryClient } from "@tanstack/react-query"

export const sessionQueryKey = ["auth", "me"] as const

export function createQueryClient(options?: { focus?: boolean }): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 30_000,
        refetchOnWindowFocus: options?.focus ?? true,
      },
      mutations: { retry: false },
    },
  })
}
