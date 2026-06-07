import { test, expect } from '@playwright/test';

test.describe('Login Page Visual Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    // Wait for components to be ready
    await page.waitForLoadState('networkidle');
  });

  test('Login page - Light Mode', async ({ page }) => {
    // Ensure light mode
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.classList.remove('dark');
    });
    
    // Check elements visibility
    await expect(page.locator('h2')).toContainText('Welcome back');
    await expect(page.locator('md-outlined-text-field').first()).toBeVisible();
    await expect(page.locator('md-filled-button')).toContainText('Sign In');

    // Take screenshot
    await expect(page).toHaveScreenshot('login-light.png', {
      maxDiffPixelRatio: 0.1,
      fullPage: true,
    });
  });

  test('Login page - Dark Mode', async ({ page }) => {
    // Switch to dark mode
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark');
    });
    
    // Brief wait for theme transition if any
    await page.waitForTimeout(500);

    // Take screenshot
    await expect(page).toHaveScreenshot('login-dark.png', {
      maxDiffPixelRatio: 0.1,
      fullPage: true,
    });
  });

  test('Login page - Error State', async ({ page }) => {
    // Trigger error by submitting form
    const emailField = page.locator('md-outlined-text-field').first();
    const passwordField = page.locator('md-outlined-text-field').last();
    const submitButton = page.locator('md-filled-button');

    await emailField.click();
    await page.keyboard.type('admin@backoffice.dev');
    
    await passwordField.click();
    await page.keyboard.type('wrong-password');
    
    await submitButton.click();
    
    // Wait for error message (the class name I used in the template)
    const errorContainer = page.locator('.bg-error-container');
    await expect(errorContainer).toBeVisible({ timeout: 10000 });
    
    // Take screenshot of error state
    await expect(page).toHaveScreenshot('login-error.png', {
      maxDiffPixelRatio: 0.1,
    });
  });
});
