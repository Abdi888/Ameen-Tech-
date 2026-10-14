export type Profile = {
  user: {
    id: string
    email: string
    first_name: string
    last_name: string
    phone: string
    status: string
  }
  memberships: {
    id: string
    tenant_id: string
    tenant_name: string
    status: string
    roles: { id: string; name: string }[]
  }[]
  tenant: { id: string; name: string } | null
  roles: string[]
  permissions: string[]
}

export function displayName(user: Profile["user"]): string {
  const name = `${user.first_name} ${user.last_name}`.trim()
  return name || user.email
}
