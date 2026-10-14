import { LogoutButton } from "../../shared/components/LogoutButton"
import { AccessDenied } from "../../shared/components/Status"

export function PlatformBoundary() {
  return (
    <div className="platform">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="platform-header">
        <p className="wordmark">Ameen Retail</p>
        <LogoutButton />
      </header>
      <main id="main" className="platform-main">
        <AccessDenied />
      </main>
    </div>
  )
}
