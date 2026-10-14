export type Destination = {
  path: string
  title: string
  area: string
  navLabel?: string
  navTo?: string
  allow: (permissions: ReadonlySet<string>) => boolean
}

function has(key: string) {
  return (permissions: ReadonlySet<string>) => permissions.has(key)
}

function hasEvery(...keys: string[]) {
  return (permissions: ReadonlySet<string>) => keys.every((key) => permissions.has(key))
}

function hasSome(...keys: string[]) {
  return (permissions: ReadonlySet<string>) => keys.some((key) => permissions.has(key))
}

/** Document 07 §5 entry routes. Paths are relative to `/app`. */
export const destinations: Destination[] = [
  {
    path: "dashboard",
    title: "Dashboard",
    area: "Dashboard",
    navLabel: "Dashboard",
    allow: has("dashboard.view"),
  },
  {
    path: "sales",
    title: "Sales",
    area: "Sales",
    navLabel: "Sales",
    allow: has("sales.view"),
  },
  {
    path: "sales/new",
    title: "New sale",
    area: "Sales",
    navLabel: "New sale",
    allow: has("sales.create"),
  },
  {
    path: "sales/returns",
    title: "Returns",
    area: "Sales",
    navLabel: "Returns",
    allow: has("sales_returns.view"),
  },
  {
    path: "sales/:id",
    title: "Sale",
    area: "Sales",
    allow: has("sales.view"),
  },
  {
    path: "pos",
    title: "POS",
    area: "POS",
    navLabel: "POS",
    allow: has("pos.view"),
  },
  {
    path: "pos/sessions",
    title: "Sessions",
    area: "POS",
    navLabel: "Sessions",
    allow: has("pos.view_sessions"),
  },
  {
    // Document 07 §5: `/pos/sessions/:id`. No session API in Phase 7, so this is
    // an empty guarded destination only. Do not invent a sentinel id such as
    // `current` for the sidebar — parametric screens are reached with a real id.
    path: "pos/sessions/:id",
    title: "Cash movement",
    area: "POS",
    allow: hasSome("pos.cash_in", "pos.cash_out"),
  },
  {
    path: "customers",
    title: "Customers",
    area: "Customers",
    navLabel: "Customers",
    allow: has("customers.view"),
  },
  {
    path: "products",
    title: "Products",
    area: "Products",
    navLabel: "Products",
    allow: has("products.view"),
  },
  {
    path: "products/categories",
    title: "Categories",
    area: "Products",
    navLabel: "Categories",
    allow: has("product_categories.view"),
  },
  {
    path: "inventory",
    title: "Inventory",
    area: "Inventory",
    navLabel: "Inventory",
    allow: has("inventory.view"),
  },
  {
    path: "inventory/movements",
    title: "Movements",
    area: "Inventory",
    navLabel: "Movements",
    allow: has("inventory.view_movements"),
  },
  {
    path: "inventory/adjustments",
    title: "Adjustments",
    area: "Inventory",
    navLabel: "Adjustments",
    allow: hasEvery("inventory.view", "inventory.adjust"),
  },
  {
    path: "inventory/transfers",
    title: "Transfers",
    area: "Inventory",
    navLabel: "Transfers",
    allow: hasEvery("inventory.view", "inventory.transfer"),
  },
  {
    path: "reports/finance",
    title: "Financial reports",
    area: "Reports",
    navLabel: "Financial reports",
    allow: has("reports.finance.view"),
  },
  {
    path: "settings/users",
    title: "Users",
    area: "Users",
    navLabel: "Users",
    allow: has("users.view"),
  },
  {
    path: "settings/tax",
    title: "Tax",
    area: "Settings",
    navLabel: "Tax",
    allow: has("tax.view"),
  },
  {
    path: "audit",
    title: "Audit",
    area: "Audit",
    navLabel: "Audit",
    allow: has("audit.view"),
  },
]

export type NavEntry = {
  label: string
  to: string
  area: string
}

export function permissionSet(permissions: readonly string[]): Set<string> {
  return new Set(permissions)
}

export function visibleNavigation(permissions: readonly string[]): NavEntry[] {
  const granted = permissionSet(permissions)
  return destinations.flatMap((destination) => {
    if (!destination.navLabel || !destination.allow(granted)) return []
    const path = destination.navTo ?? destination.path
    // Path templates such as `pos/sessions/:id` are not concrete hrefs.
    if (path.includes(":")) return []
    return [
      {
        label: destination.navLabel,
        to: `/app/${path}`,
        area: destination.area,
      },
    ]
  })
}

export function defaultAppPath(permissions: readonly string[]): string {
  if (permissions.includes("dashboard.view")) return "/app/dashboard"
  return visibleNavigation(permissions)[0]?.to ?? "/app/dashboard"
}

export function safeReturnTo(value: string | null): string | null {
  if (!value) return null
  let path = value
  try {
    path = decodeURIComponent(value)
  } catch {
    return null
  }
  if (path !== value) return null
  if (!path.startsWith("/app/") && !path.startsWith("/platform/")) return null
  if (path.startsWith("//") || path.includes("\\") || path.includes("://")) return null
  if (path.includes("..") || path.includes("?") || path.includes("#") || path.includes("@")) {
    return null
  }
  return path
}

export function workspacePath(profile: { tenant: unknown; permissions: readonly string[] }, requested: string | null): string {
  const safe = safeReturnTo(requested)
  if (!profile.tenant) {
    if (safe?.startsWith("/platform/")) return safe
    return "/platform"
  }
  if (safe?.startsWith("/app/")) return safe
  return defaultAppPath(profile.permissions)
}
