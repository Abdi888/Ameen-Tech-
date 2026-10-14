import { expect, test, type Page } from "@playwright/test"

import { administrator, cashier, owner, password, platformAdmin } from "./fixtures"

const cashierLabels = ["Dashboard", "POS", "Sessions", "Customers", "Products"]

async function signIn(page: Page, email: string) {
  await page.goto("/login")
  await page.getByLabel("Email").fill(email)
  await page.getByLabel("Password").fill(password)
  await page.getByRole("button", { name: "Sign in" }).click()
}

async function openNavigation(page: Page) {
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible()
  const menu = page.getByRole("button", { name: "Open menu" })
  if (await menu.isVisible()) await menu.click()
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(1)
}

test("login page is labelled and keyboard reachable", async ({ page }) => {
  await page.goto("/login")
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible()
  await expect(page.getByLabel("Email")).toBeVisible()
  await expect(page.getByLabel("Password")).toBeVisible()
  await page.keyboard.press("Tab")
  await expect(page.getByLabel("Email")).toBeFocused()
  await page.keyboard.press("Tab")
  await expect(page.getByLabel("Password")).toBeFocused()
  const outline = await page.getByLabel("Password").evaluate((element) => {
    const style = getComputedStyle(element)
    return { style: style.outlineStyle, width: style.outlineWidth, color: style.outlineColor }
  })
  expect(outline.style).toBe("solid")
  expect(outline.width).toBe("2px")
  expect(outline.color).toBe("rgb(20, 125, 120)")
  await expectNoHorizontalOverflow(page)
})

test("unauthenticated tenant routes go to login once", async ({ page }) => {
  await page.goto("/app/dashboard")
  await expect(page).toHaveURL(/\/login\?return=%2Fapp%2Fdashboard$/)
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible()
})

test("rejected sign-in stays on the login page", async ({ page }) => {
  await page.goto("/login")
  await page.getByLabel("Email").fill("nobody@e2e.test")
  await page.getByLabel("Password").fill("not-the-real-password")
  await page.getByRole("button", { name: "Sign in" }).click()
  await expect(page.getByRole("alert")).toContainText("Invalid email or password.")
  await expect(page).toHaveURL(/\/login$/)
})

test("cashier navigation and a denied direct route", async ({ page }) => {
  await signIn(page, cashier.email)
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
  await expect(page.getByText("Harbor")).toBeVisible()
  await openNavigation(page)
  await expect(page.getByRole("navigation", { name: "Application" }).getByRole("link")).toHaveText(
    cashierLabels,
  )
  await expectNoHorizontalOverflow(page)
  await page.goto("/app/pos/sessions/11111111-1111-1111-1111-111111111111")
  await expect(page.getByRole("heading", { name: "Cash movement" })).toBeVisible()
  await expect(page.getByText("Nothing to show here yet.")).toBeVisible()
  await page.goto("/app/settings/users")
  await expect(page.getByRole("heading", { name: "Access denied" })).toBeVisible()
  await expect(page.locator("body")).not.toContainText("users.view")
  await expectNoHorizontalOverflow(page)
})

test("owner and administrator see users and tax", async ({ page }) => {
  for (const account of [owner, administrator]) {
    await signIn(page, account.email)
    await openNavigation(page)
    const navigation = page.getByRole("navigation", { name: "Application" })
    await expect(navigation.getByRole("link", { name: "Users" })).toBeVisible()
    await expect(navigation.getByRole("link", { name: "Tax" })).toBeVisible()
    await page.getByRole("button", { name: "Log out" }).click()
    await expect(page).toHaveURL(/\/login$/)
  }
})

test("platform administrator has no tenant workspace", async ({ page }) => {
  await signIn(page, platformAdmin.email)
  await expect(page).toHaveURL(/\/platform$/)
  await expect(page.getByRole("heading", { name: "Access denied" })).toBeVisible()
  await expect(page.getByRole("navigation")).toHaveCount(0)
  await expectNoHorizontalOverflow(page)
  await page.goto("/app/dashboard")
  await expect(page).toHaveURL(/\/platform$/)
  await expect(page.getByRole("navigation")).toHaveCount(0)
})

test("logout revokes the workspace session", async ({ page }) => {
  await signIn(page, owner.email)
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible()
  await page.getByRole("button", { name: "Log out" }).click()
  await expect(page).toHaveURL(/\/login$/)
  await page.goto("/app/dashboard")
  await expect(page).toHaveURL(/\/login\?return=/)
})
