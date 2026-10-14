import { ApiRequestError, type ApiFieldError, unavailableMessage } from "./errors"

const CSRF_COOKIE = "csrftoken"
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"])

let provenTenantId: string | null = null

export function setProvenTenantId(tenantId: string | null): void {
  provenTenantId = tenantId
}

export function resetProvenTenantId(): void {
  provenTenantId = null
}

function readCookie(name: string): string | null {
  const prefix = `${name}=`
  for (const part of document.cookie.split("; ")) {
    if (part.startsWith(prefix)) return decodeURIComponent(part.slice(prefix.length))
  }
  return null
}

async function ensureCsrfCookie(): Promise<string> {
  const existing = readCookie(CSRF_COOKIE)
  if (existing) return existing
  await fetch("/api/v1/health", { credentials: "include" })
  const token = readCookie(CSRF_COOKIE)
  if (!token) {
    throw new ApiRequestError(403, [
      {
        code: "PERMISSION_DENIED",
        message: "CSRF verification failed.",
        field: null,
      },
    ])
  }
  return token
}

function fieldErrors(value: unknown): ApiFieldError[] {
  if (!value || typeof value !== "object" || !("errors" in value)) {
    return [{ code: "INTERNAL_ERROR", message: unavailableMessage(), field: null }]
  }
  const errors = (value as { errors?: unknown }).errors
  if (!Array.isArray(errors) || errors.length === 0) {
    return [{ code: "INTERNAL_ERROR", message: unavailableMessage(), field: null }]
  }
  return errors.map((item) => {
    const record = item as { code?: unknown; message?: unknown; field?: unknown }
    return {
      code: typeof record.code === "string" ? record.code : "INTERNAL_ERROR",
      message: typeof record.message === "string" ? record.message : unavailableMessage(),
      field: typeof record.field === "string" ? record.field : null,
    }
  })
}

export async function apiRequest<T>(
  path: string,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  const method = options.method ?? "GET"
  const headers = new Headers({
    Accept: "application/json",
    "X-Request-Id": crypto.randomUUID(),
  })
  if (options.body !== undefined) headers.set("Content-Type", "application/json")
  if (!SAFE_METHODS.has(method)) headers.set("X-CSRFToken", await ensureCsrfCookie())
  if (provenTenantId) headers.set("X-Tenant-Id", provenTenantId)

  let response: Response
  try {
    response = await fetch(path, {
      method,
      credentials: "include",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: AbortSignal.timeout(15_000),
    })
  } catch {
    throw new ApiRequestError(0, [
      { code: "SERVICE_UNAVAILABLE", message: unavailableMessage(), field: null },
    ])
  }

  const text = await response.text()
  let payload: unknown = null
  if (text) {
    try {
      payload = JSON.parse(text) as unknown
    } catch {
      throw new ApiRequestError(response.status, [
        { code: "INTERNAL_ERROR", message: unavailableMessage(), field: null },
      ])
    }
  }
  if (!response.ok) throw new ApiRequestError(response.status, fieldErrors(payload))
  if (!payload || typeof payload !== "object" || !("data" in payload)) {
    throw new ApiRequestError(response.status, [
      { code: "INTERNAL_ERROR", message: unavailableMessage(), field: null },
    ])
  }
  return (payload as { data: T }).data
}
