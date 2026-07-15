import { test, expect } from "@playwright/test";

function uniqueEmail() {
  return `e2e-${Date.now()}@example.com`;
}

const PASSWORD = "e2e-password-123";

test.describe("Authentication", () => {
  test("a new user can register and is redirected to chat", async ({ page }) => {
    const email = uniqueEmail();

    await page.goto("/register");
    await expect(page).toHaveTitle(/AI Document Q&A/);

    await page.fill("#email", email);
    await page.fill("#password", PASSWORD);
    await page.fill("#confirmPassword", PASSWORD);
    await page.click('button:has-text("Create account")');

    await page.waitForURL("/chat", { timeout: 10_000 });
    await expect(page).toHaveURL("/chat");
    await expect(page.locator('button:has-text("Log out")')).toBeVisible();
  });

  test("an existing user can log in and access protected routes", async ({ page }) => {
    const email = uniqueEmail();

    // Register via UI first
    await page.goto("/register");
    await page.fill("#email", email);
    await page.fill("#password", PASSWORD);
    await page.fill("#confirmPassword", PASSWORD);
    await page.click('button:has-text("Create account")');
    await page.waitForURL("/chat", { timeout: 10_000 });

    // Log out
    await page.click('button:has-text("Log out")');
    await page.waitForURL("/login", { timeout: 10_000 });
    await expect(page).toHaveURL("/login");

    // Log back in
    await page.fill("#email", email);
    await page.fill("#password", PASSWORD);
    await page.click('button:has-text("Sign in")');

    await page.waitForURL("/chat", { timeout: 10_000 });
    await expect(page).toHaveURL("/chat");

    // Navigate to a protected route
    await page.goto("/documents");
    await expect(page).toHaveURL("/documents");
  });

  test("unauthenticated users are redirected to login from protected routes", async ({ page }) => {
    await page.goto("/documents");
    await page.waitForURL("/login", { timeout: 10_000 });
    await expect(page).toHaveURL("/login");
  });
});
