import { test, expect } from '@playwright/test';

/**
 * Internal Pages Visual Regression Tests
 * Covers Tenant Management UI: Stitch high-density layout validation.
 *
 * Strategy:
 * - Mock BFF /api/tenants/ to avoid server dependency
 * - Inject auth state via sessionStorage to bypass Keycloak
 * - Validate Stitch component presence before screenshot comparison
 */

const MOCK_TENANTS = [
  {
    id: 1,
    name: 'Acme Corp',
    country: 'USA',
    status: 'active',
    default_language: 'en',
    default_currency: 'USD',
    default_units: 'imperial',
    products: ['Core', 'Analytics'],
    logo_url: null,
    primary_color: '#1a73e8',
    secondary_color: '#5f6368',
    accent_color: '#34a853',
    font_family: 'Inter',
    font_weight: '400',
    domain: 'acme.backoffice.dev',
    created_at: '2023-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: 'Globex',
    country: 'Spain',
    status: 'suspended',
    default_language: 'es',
    default_currency: 'EUR',
    default_units: 'metric',
    products: ['Core'],
    logo_url: null,
    primary_color: '#e8371a',
    secondary_color: '#5f6368',
    accent_color: '#fbbc04',
    font_family: 'Roboto',
    font_weight: '400',
    domain: '',
    created_at: '2023-02-01T00:00:00Z'
  }
];

test.describe('Internal Pages — Stitch Design', () => {
  test.beforeEach(async ({ page }) => {
    // Print browser console logs and errors directly to E2E test output
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
    page.on('pageerror', err => console.error('BROWSER ERROR:', err.message));

    // Mock BFF tenants endpoint (portal calls http://localhost:3000/tenants/)
    await page.route('**/tenants/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_TENANTS)
      });
    });

    // Mock BFF products endpoint (portal calls http://localhost:3000/products/)
    await page.route('**/products/**', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 'Core', name: 'Core', status: 'active' },
          { id: 'Analytics', name: 'Analytics', status: 'active' }
        ])
      });
    });

    // Inject auth session to bypass Keycloak
    await page.addInitScript(() => {
      const mockAuth = {
        token: 'mock-jwt-token',
        user: { name: 'Test Admin', email: 'admin@test.com', sub: 'mock-sub' },
        roles: ['PlatformAdmin'],
        isAuthenticated: true,
        isLoading: false
      };
      window.sessionStorage.setItem('auth', JSON.stringify(mockAuth));
    });

    await page.goto('/tenants');
    await page.waitForLoadState('networkidle');
  });

  // ----- Layout: Light Mode -----

  test('Tenants View — Light Mode layout', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.classList.remove('dark');
    });
    await page.waitForTimeout(400);

    // Assert Stitch structural elements are present
    await expect(page.locator('table')).toBeVisible();
    await expect(page.locator('text=Acme Corp')).toBeVisible();
    await expect(page.locator('text=Globex')).toBeVisible();

    // Bento summary cards
    await expect(page.locator('text=Active Tenants')).toBeVisible();
    await expect(page.locator('text=Total Products')).toBeVisible();
    await expect(page.locator('text=System Health')).toBeVisible();

    // Table filter tabs
    await expect(page.locator('text=All Tenants')).toBeVisible();

    // Page header with Stitch title typography
    await expect(page.locator('.page-title')).toBeVisible();
    await expect(page.locator('.page-title')).toContainText('Tenant Management');

    // Status chips
    const statusChips = page.locator('.status-chip');
    await expect(statusChips.first()).toBeVisible();

    // Action buttons (icon-based, not md-icon-button)
    const inventoryBtns = page.locator('button[title="Manage Products"]');
    await expect(inventoryBtns.first()).toBeVisible();

    await expect(page).toHaveScreenshot('tenants-view-light.png', {
      maxDiffPixelRatio: 0.1,
      fullPage: true,
    });
  });

  // ----- Layout: Dark Mode -----

  test('Tenants View — Dark Mode layout', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark');
    });
    await page.waitForTimeout(400);

    await expect(page.locator('table')).toBeVisible();

    // Verify status chips are present (both active and suspended)
    const statusChips = page.locator('.status-chip');
    await expect(statusChips.first()).toBeVisible();

    await expect(page).toHaveScreenshot('tenants-view-dark.png', {
      maxDiffPixelRatio: 0.1,
      fullPage: true,
    });
  });

  // ----- Drawer: Create Mode -----

  test('Tenant Drawer — Create mode (General Info tab)', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.classList.remove('dark');
    });

    // Open create drawer via Stitch button
    await page.click('text=Create New Tenant');
    await page.waitForSelector('.drawer-content', { state: 'visible' });
    await page.waitForTimeout(400);

    // Verify drawer Stitch structure
    await expect(page.locator('.drawer-title')).toContainText('Create Tenant');
    await expect(page.locator('.drawer-subtitle')).toBeVisible();

    // Verify md-tabs are rendered
    await expect(page.locator('md-tabs')).toBeVisible();

    // Verify StitchTextField (md-outlined-text-field) is rendered in form
    await expect(page.locator('md-outlined-text-field').first()).toBeVisible();

    // Verify StitchButton for footer actions
    await expect(page.locator('md-filled-button').first()).toBeVisible();

    await expect(page).toHaveScreenshot('tenant-drawer-create.png', {
      maxDiffPixelRatio: 0.1,
    });
  });

  // ----- Drawer: Whitelabel Tab -----

  test('Tenant Drawer — Whitelabel tab', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'light');
      document.documentElement.classList.remove('dark');
    });

    await page.click('text=Create New Tenant');
    await page.waitForSelector('.drawer-content', { state: 'visible' });

    // Navigate to Whitelabel tab
    await page.click('md-primary-tab:has-text("Whitelabel")');
    await page.waitForTimeout(300);

    // Verify section labels are present
    await expect(page.locator('.form-section-label').first()).toBeVisible();

    // Verify color inputs and text fields are rendered
    await expect(page.locator('md-outlined-text-field').first()).toBeVisible();

    // Verify preview card is present
    await expect(page.locator('.preview-card')).toBeVisible();

    await expect(page).toHaveScreenshot('tenant-drawer-whitelabel.png', {
      maxDiffPixelRatio: 0.1,
    });
  });

  // ----- Drawer: Dark Mode -----

  test('Tenant Drawer — Dark Mode elevation', async ({ page }) => {
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'dark');
      document.documentElement.classList.add('dark');
    });
    await page.waitForTimeout(400);

    await page.click('text=Create New Tenant');
    await page.waitForSelector('.drawer-content', { state: 'visible' });
    await page.waitForTimeout(400);

    await expect(page.locator('.drawer-content')).toBeVisible();

    await expect(page).toHaveScreenshot('tenant-drawer-dark.png', {
      maxDiffPixelRatio: 0.1,
    });
  });
});
