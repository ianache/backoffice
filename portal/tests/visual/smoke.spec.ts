import { test, expect } from '@playwright/test';

test('login page visual smoke test', async ({ page }) => {
  // Go to the login page
  await page.goto('/login');
  
  // Wait for the redirecting text to be visible (before it redirects)
  // Or just wait a bit.
  await page.waitForLoadState('networkidle');
  
  // Take a screenshot
  await expect(page).toHaveScreenshot('login-page.png', {
    maxDiffPixelRatio: 0.1,
  });
});

test('unauthorized page visual smoke test', async ({ page }) => {
  await page.goto('/unauthorized');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('unauthorized-page.png');
});
