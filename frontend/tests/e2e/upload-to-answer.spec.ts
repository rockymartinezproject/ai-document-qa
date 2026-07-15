import { test, expect } from "@playwright/test";
import path from "path";

function uniqueEmail() {
  return `e2e-${Date.now()}@example.com`;
}

const PASSWORD = "e2e-password-123";

const SAMPLE_PDF = path.join(__dirname, "fixtures", "generate-sample-pdf.pdf");

test.describe("Upload to answer", () => {
  test("uploads a PDF and receives a streamed answer", async ({ page }) => {
    const email = uniqueEmail();

    // 1. Register a new user
    await page.goto("/register");
    await page.fill("#email", email);
    await page.fill("#password", PASSWORD);
    await page.fill("#confirmPassword", PASSWORD);
    await page.click('button:has-text("Create account")');
    await page.waitForURL("/chat", { timeout: 10_000 });

    // 2. Upload the sample PDF
    await page.goto("/upload");
    await page.locator('input[type="file"]').setInputFiles(SAMPLE_PDF);

    const docCard = page.locator("text=generate-sample-pdf.pdf").first();
    await expect(docCard).toBeVisible({ timeout: 15_000 });
    await expect(page.locator('span:has-text("indexed")').first()).toBeVisible({
      timeout: 15_000,
    });

    // 3. Ask a question about the uploaded document
    await page.goto("/chat");

    // Ensure the mock provider is selected (other providers may not be reachable in CI).
    const providerSelect = page.locator("select").first();
    await providerSelect.selectOption("mock");

    await page.fill(
      'textarea[placeholder="Type a message..."]',
      "What is the capital of France?"
    );
    await page.click('button:has-text("Send")');

    // 4. Verify an assistant answer appears. With the mock provider and indexed
    // chunks this will contain "Mock LLM"; with no retrieved chunks it will be
    // the fallback message.
    const answer = page.locator("[class*='whitespace-pre-wrap']").last();
    await expect(answer).toContainText(/Mock LLM|relevant information|couldn't find/i, {
      timeout: 30_000,
    });
  });
});
