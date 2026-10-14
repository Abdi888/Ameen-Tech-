import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import {
  cashierPermissions,
  envelope,
  errorEnvelope,
  header,
  jsonResponse,
  profile,
  renderAt,
  stubFetch,
} from "./render"

const fullPermissions = [
  "dashboard.view",
  "sales.view",
  "sales.create",
  "sales_returns.view",
  "pos.view",
  "pos.view_sessions",
  "pos.cash_in",
  "customers.view",
  "products.view",
  "product_categories.view",
  "inventory.view",
  "inventory.view_movements",
  "inventory.adjust",
  "inventory.transfer",
  "reports.finance.view",
  "users.view",
  "tax.view",
  "audit.view",
]

describe("application shell", () => {
  beforeEach(() => {
    document.cookie = "csrftoken=test-csrf"
  })

  it("does not render the workspace before the session is known", async () => {
    let release: (response: Response) => void = () => undefined
    const pending = new Promise<Response>((resolve) => {
      release = resolve
    })
    stubFetch((url) => (url.includes("/auth/me") ? pending : jsonResponse(200, envelope({}))))
    renderAt("/app/dashboard")
    expect(screen.getByRole("status")).toHaveTextContent("Loading")
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument()
    release(jsonResponse(200, envelope(profile({ permissions: cashierPermissions }))))
    expect(await screen.findByRole("navigation", { name: "Application" })).toBeInTheDocument()
  })

  it("shows only the cashier destinations", async () => {
    stubFetch(() =>
      jsonResponse(200, envelope(profile({ roles: ["Administrator"], permissions: cashierPermissions }))),
    )
    renderAt("/app/dashboard")
    const navigation = await screen.findByRole("navigation", { name: "Application" })
    expect(within(navigation).getAllByRole("link").map((link) => link.textContent)).toEqual([
      "Dashboard",
      "POS",
      "Sessions",
      "Customers",
      "Products",
    ])
    expect(within(navigation).queryByRole("link", { name: "Cash movement" })).not.toBeInTheDocument()
    expect(within(navigation).queryByRole("link", { name: "Users" })).not.toBeInTheDocument()
    expect(screen.getByText("Harbor")).toBeInTheDocument()
  })

  it("opens cash movement as an empty destination for a session id path", async () => {
    stubFetch(() => jsonResponse(200, envelope(profile({ permissions: cashierPermissions }))))
    renderAt("/app/pos/sessions/11111111-1111-1111-1111-111111111111")
    expect(await screen.findByRole("heading", { name: "Cash movement" })).toBeInTheDocument()
    expect(screen.getByText("Nothing to show here yet.")).toBeInTheDocument()
    expect(screen.queryByText("current")).not.toBeInTheDocument()
  })

  it("follows the permission set for an administrator label", async () => {
    stubFetch(() =>
      jsonResponse(
        200,
        envelope(profile({ roles: ["Cashier"], permissions: fullPermissions })),
      ),
    )
    renderAt("/app/dashboard")
    const navigation = await screen.findByRole("navigation", { name: "Application" })
    expect(within(navigation).getByRole("link", { name: "Users" })).toBeInTheDocument()
    expect(within(navigation).getByRole("link", { name: "Tax" })).toBeInTheDocument()
  })

  it("denies a direct route without exposing the permission key", async () => {
    stubFetch(() => jsonResponse(200, envelope(profile({ permissions: ["products.view"] }))))
    renderAt("/app/dashboard")
    expect(await screen.findByRole("heading", { name: "Access denied" })).toBeInTheDocument()
    expect(screen.getByText("You do not have access to this page.")).toBeInTheDocument()
    expect(document.body.textContent).not.toContain("dashboard.view")
  })

  it("sends an unauthenticated visit to login and preserves a safe return path", async () => {
    stubFetch(() =>
      jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required.")),
    )
    const { router } = renderAt("/app/products")
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe("/login")
    expect(router.state.location.search).toBe("?return=%2Fapp%2Fproducts")
  })

  it("clears cached data when the session is rejected", async () => {
    let release: (response: Response) => void = () => undefined
    const pending = new Promise<Response>((resolve) => {
      release = resolve
    })
    stubFetch((url) => (url.includes("/auth/me") ? pending : jsonResponse(200, envelope({}))))
    const { client } = renderAt("/app/dashboard")
    client.setQueryData(["products", "tenant-1"], ["secret"])
    release(jsonResponse(401, errorEnvelope("AUTH_TOKEN_EXPIRED", "Session expired.")))
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument()
    await waitFor(() => expect(client.getQueryData(["products", "tenant-1"])).toBeUndefined())
    expect(screen.getByLabelText("Email")).toBeInTheDocument()
    expect(screen.getByLabelText("Password")).toBeInTheDocument()
  })

  it("keeps the session when a page is forbidden", async () => {
    stubFetch(() => jsonResponse(200, envelope(profile({ permissions: cashierPermissions }))))
    const { client } = renderAt("/app/settings/users")
    client.setQueryData(["products", "tenant-1"], ["secret"])
    expect(await screen.findByRole("heading", { name: "Access denied" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument()
    expect(client.getQueryData(["products", "tenant-1"])).toEqual(["secret"])
    expect(document.body.textContent).not.toContain("users.view")
  })

  it("shows an error instead of an empty page when the profile cannot be loaded", async () => {
    stubFetch(() => jsonResponse(503, errorEnvelope("SERVICE_UNAVAILABLE", "The service is unavailable. Try again.")))
    renderAt("/app/dashboard")
    expect(await screen.findByRole("heading", { name: "Something went wrong" })).toBeInTheDocument()
    expect(screen.queryByText("Nothing to show here yet.")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument()
  })

  it("logs out and clears the query cache", async () => {
    const user = userEvent.setup()
    let signedIn = true
    stubFetch((url) => {
      if (url.includes("/auth/logout")) {
        signedIn = false
        return jsonResponse(200, envelope({}))
      }
      if (url.includes("/auth/me")) {
        return signedIn
          ? jsonResponse(200, envelope(profile()))
          : jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required."))
      }
      return jsonResponse(200, envelope({}))
    })
    const { client, router } = renderAt("/app/dashboard")
    expect(await screen.findByRole("button", { name: "Log out" })).toBeInTheDocument()
    client.setQueryData(["products", "tenant-1"], ["secret"])
    await user.click(screen.getByRole("button", { name: "Log out" }))
    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe("/login")
    expect(client.getQueryData(["products", "tenant-1"])).toBeUndefined()
  })

  it("keeps a platform administrator out of the tenant workspace", async () => {
    stubFetch(() =>
      jsonResponse(
        200,
        envelope(
          profile({
            tenant: null,
            memberships: [],
            permissions: [],
            roles: [],
          }),
        ),
      ),
    )
    const { router } = renderAt("/app/dashboard")
    expect(await screen.findByRole("heading", { name: "Access denied" })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe("/platform")
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument()
    expect(screen.queryByText("Harbor")).not.toBeInTheDocument()
  })

  it("does not offer a tenant switch when the server has not chosen a tenant", async () => {
    stubFetch(() =>
      jsonResponse(
        200,
        envelope(
          profile({
            tenant: null,
            permissions: [],
            memberships: [
              {
                id: "m1",
                tenant_id: "t1",
                tenant_name: "Harbor",
                status: "ACTIVE",
                roles: [],
              },
              {
                id: "m2",
                tenant_id: "t2",
                tenant_name: "Market",
                status: "ACTIVE",
                roles: [],
              },
            ],
          }),
        ),
      ),
    )
    renderAt("/app/dashboard")
    expect(await screen.findByRole("heading", { name: "Workspace unavailable" })).toBeInTheDocument()
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Harbor" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Market" })).not.toBeInTheDocument()
  })

  it("keeps tenant navigation off the platform route", async () => {
    stubFetch(() => jsonResponse(200, envelope(profile({ permissions: fullPermissions }))))
    renderAt("/platform")
    expect(await screen.findByRole("heading", { name: "Access denied" })).toBeInTheDocument()
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument()
    expect(screen.queryByRole("link", { name: "Users" })).not.toBeInTheDocument()
  })
})

describe("login", () => {
  beforeEach(() => {
    document.cookie = "csrftoken=test-csrf"
    stubFetch((url) => {
      if (url.includes("/auth/me")) {
        return jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required."))
      }
      return jsonResponse(200, envelope({ status: "ok", database: "ok" }))
    })
  })

  it("labels the controls and reports a rejected sign-in", async () => {
    const user = userEvent.setup()
    const calls: string[] = []
    stubFetch((url, init) => {
      calls.push(url)
      if (url.includes("/auth/login")) {
        expect(header(init, "X-CSRFToken")).toBe("test-csrf")
        expect(header(init, "X-Tenant-Id")).toBeNull()
        expect(JSON.parse(String(init?.body))).toEqual({
          email: "amina@harbor.test",
          password: "wrong-password",
        })
        return jsonResponse(401, errorEnvelope("AUTH_INVALID_TOKEN", "Invalid email or password."))
      }
      return jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required."))
    })
    const { router } = renderAt("/login?return=https://evil.example")
    expect(await screen.findByLabelText("Email")).toBeInTheDocument()
    expect(screen.getByLabelText("Password")).toBeInTheDocument()
    await user.type(screen.getByLabelText("Email"), "amina@harbor.test")
    await user.type(screen.getByLabelText("Password"), "wrong-password")
    await user.click(screen.getByRole("button", { name: "Sign in" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.")
    expect(router.state.location.pathname).toBe("/login")
    expect(calls.filter((url) => url.includes("/auth/login"))).toHaveLength(1)
  })

  it("shows validation errors and does not retry a rate limit", async () => {
    const user = userEvent.setup()
    let loginCalls = 0
    stubFetch((url) => {
      if (url.includes("/auth/login")) {
        loginCalls += 1
        return jsonResponse(429, errorEnvelope("AUTH_INVALID_TOKEN", "Too many attempts. Try again later."))
      }
      return jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required."))
    })
    renderAt("/login")
    await user.click(await screen.findByRole("button", { name: "Sign in" }))
    expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument()
    expect(loginCalls).toBe(0)
    await user.type(screen.getByLabelText("Email"), "amina@harbor.test")
    await user.type(screen.getByLabelText("Password"), "correct-horse")
    await user.click(screen.getByRole("button", { name: "Sign in" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("Too many attempts. Try again later.")
    expect(loginCalls).toBe(1)
  })

  it("stays on the form when CSRF fails or the service is down", async () => {
    const user = userEvent.setup()
    stubFetch((url) => {
      if (url.includes("/auth/login")) {
        return jsonResponse(403, errorEnvelope("PERMISSION_DENIED", "CSRF verification failed."))
      }
      return jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required."))
    })
    renderAt("/login")
    await user.type(await screen.findByLabelText("Email"), "amina@harbor.test")
    await user.type(screen.getByLabelText("Password"), "correct-horse")
    await user.click(screen.getByRole("button", { name: "Sign in" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("CSRF verification failed.")

    vi.stubGlobal("fetch", () => Promise.reject(new TypeError("offline")))
    await user.click(screen.getByRole("button", { name: "Sign in" }))
    expect(await screen.findByRole("alert")).toHaveTextContent("The service is unavailable. Try again.")
  })

  it("opens the requested tenant page after sign-in", async () => {
    const user = userEvent.setup()
    stubFetch((url) => {
      if (url.includes("/auth/login")) {
        return jsonResponse(200, envelope(profile({ permissions: ["products.view", "dashboard.view"] })))
      }
      if (url.includes("/auth/me")) {
        return jsonResponse(401, errorEnvelope("AUTH_REQUIRED", "Authentication is required."))
      }
      return jsonResponse(200, envelope({ status: "ok" }))
    })
    const { router } = renderAt("/login?return=/app/products")
    await user.type(await screen.findByLabelText("Email"), "amina@harbor.test")
    await user.type(screen.getByLabelText("Password"), "correct-horse")
    await user.click(screen.getByRole("button", { name: "Sign in" }))
    expect(await screen.findByRole("heading", { name: "Products" })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe("/app/products")
  })
})
