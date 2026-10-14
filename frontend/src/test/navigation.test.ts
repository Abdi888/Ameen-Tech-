import { describe, expect, it } from "vitest"

import { safeReturnTo, visibleNavigation, workspacePath } from "../shared/navigation/items"
import { cashierPermissions } from "./render"

describe("safe return paths", () => {
  it("accepts tenant and platform paths only", () => {
    expect(safeReturnTo("/app/dashboard")).toBe("/app/dashboard")
    expect(safeReturnTo("/platform/tenants")).toBe("/platform/tenants")
    expect(safeReturnTo("https://evil.example")).toBeNull()
    expect(safeReturnTo("//evil.example")).toBeNull()
    expect(safeReturnTo("/app/../platform")).toBeNull()
    expect(safeReturnTo("%2F%2Fevil.example")).toBeNull()
    expect(safeReturnTo("/login")).toBeNull()
    expect(safeReturnTo("/app/dashboard?next=https://evil.example")).toBeNull()
  })

  it("sends a signed-in tenant user to the requested app path", () => {
    const next = workspacePath({ tenant: { id: "t" }, permissions: cashierPermissions }, "/app/products")
    expect(next).toBe("/app/products")
  })

  it("ignores an external return path", () => {
    const next = workspacePath(
      { tenant: { id: "t" }, permissions: ["dashboard.view"] },
      "https://evil.example/app/dashboard",
    )
    expect(next).toBe("/app/dashboard")
  })
})

describe("navigation permissions", () => {
  it("shows the cashier entries and ignores the role name", () => {
    const labels = visibleNavigation(cashierPermissions).map((entry) => entry.label)
    // Document 07 §5 Cash movement is `/pos/sessions/:id`. Without a session id
    // it is not a sidebar link; the empty destination stays on the route pattern.
    expect(labels).toEqual(["Dashboard", "POS", "Sessions", "Customers", "Products"])
  })
})
