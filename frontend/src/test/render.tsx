import "@testing-library/jest-dom/vitest"
import { QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
import { createMemoryRouter, RouterProvider } from "react-router"
import { vi } from "vitest"

import { appRoutes } from "../app/router"
import type { Profile } from "../shared/session/profile"
import { createQueryClient } from "../shared/session/queryClient"

export const cashierPermissions = [
  "dashboard.view",
  "pos.view",
  "pos.create_sale",
  "pos.open_register",
  "pos.close_register",
  "pos.view_sessions",
  "pos.cash_in",
  "pos.cash_out",
  "pos.reprint",
  "customers.view",
  "customers.create",
  "products.view",
]

export function profile(overrides: Partial<Profile> = {}): Profile {
  return {
    user: {
      id: "user-1",
      email: "amina@harbor.test",
      first_name: "Amina",
      last_name: "Hassan",
      phone: "",
      status: "ACTIVE",
      ...overrides.user,
    },
    memberships: overrides.memberships ?? [
      {
        id: "membership-1",
        tenant_id: "tenant-1",
        tenant_name: "Harbor",
        status: "ACTIVE",
        roles: [],
      },
    ],
    tenant: overrides.tenant === undefined ? { id: "tenant-1", name: "Harbor" } : overrides.tenant,
    roles: overrides.roles ?? [],
    permissions: overrides.permissions ?? ["dashboard.view"],
  }
}

export function envelope(data: unknown) {
  return { success: true, data, meta: {} }
}

export function errorEnvelope(code: string, message: string, field: string | null = null) {
  return { success: false, data: null, meta: {}, errors: [{ code, message, field }] }
}

export function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

export function header(init: RequestInit | undefined, name: string): string | null {
  return new Headers(init?.headers).get(name)
}

export function stubFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>,
) {
  vi.stubGlobal("fetch", (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url
    return Promise.resolve(handler(url, init))
  })
}

export function renderAt(path: string) {
  const client = createQueryClient({ focus: false })
  const router = createMemoryRouter(appRoutes, { initialEntries: [path] })
  const view = render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { client, router, ...view }
}
