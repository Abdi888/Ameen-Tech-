import { cleanup } from "@testing-library/react"
import { afterEach, vi } from "vitest"

import { resetProvenTenantId } from "../shared/api/client"

afterEach(() => {
  cleanup()
  resetProvenTenantId()
  document.cookie = "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT"
  vi.unstubAllGlobals()
})
