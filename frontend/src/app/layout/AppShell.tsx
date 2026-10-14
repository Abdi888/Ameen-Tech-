import { useEffect, useState } from "react"
import { NavLink, Outlet, useLocation } from "react-router"

import { LogoutButton } from "../../shared/components/LogoutButton"
import { visibleNavigation } from "../../shared/navigation/items"
import { displayName } from "../../shared/session/profile"
import { useSession } from "../../shared/session/useSession"

export function AppShell() {
  const session = useSession()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const profile = session.data

  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  if (!profile?.tenant) return null
  const entries = visibleNavigation(profile.permissions)
  const groups: { area: string; entries: typeof entries }[] = []
  for (const entry of entries) {
    const current = groups[groups.length - 1]
    if (!current || current.area !== entry.area) groups.push({ area: entry.area, entries: [entry] })
    else current.entries.push(entry)
  }

  return (
    <div className="shell">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="shell-header">
        <button
          type="button"
          className="button button-secondary menu-button"
          aria-expanded={open}
          aria-controls="app-nav"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? "Close menu" : "Open menu"}
        </button>
        <p className="wordmark">Ameen Retail</p>
        <p className="tenant-name">{profile.tenant.name}</p>
        <p className="user-name">{displayName(profile.user)}</p>
        <LogoutButton />
      </header>
      <div className="shell-body">
        <nav id="app-nav" className={open ? "shell-nav is-open" : "shell-nav"} aria-label="Application">
          {groups.map((group) => (
            <div key={group.area}>
              {group.entries.length > 1 || group.entries[0]?.label !== group.area ? (
                <h2 className="nav-group">{group.area}</h2>
              ) : null}
              <ul className="nav-list">
                {group.entries.map((entry) => (
                  <li key={entry.to}>
                    <NavLink
                      to={entry.to}
                      end
                      className={({ isActive }) => (isActive ? "nav-link is-active" : "nav-link")}
                    >
                      {entry.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        <main id="main" className="shell-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
