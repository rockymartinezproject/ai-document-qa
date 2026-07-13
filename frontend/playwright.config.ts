import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright end-to-end test configuration.
 *
 * The config starts the backend and frontend dev servers automatically before
 * running tests. In CI the servers are always started fresh; locally an existing
 * server is reused if its health endpoint is already healthy.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      command: "cd ../backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/health",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
      env: {
        DATABASE_URL: "sqlite+aiosqlite:///./e2e.db",
        SECRET_KEY: "test-secret-key-for-e2e",
      },
    },
    {
      command: "npm run dev",
      url: "http://127.0.0.1:3000",
      timeout: 120_000,
      reuseExistingServer: !process.env.CI,
    },
  ],
});
