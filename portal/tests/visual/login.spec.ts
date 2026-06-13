import { test, expect } from '@playwright/test';

test.describe('Login Page Visual Tests', () => {
  test.describe('Default Navigation and Themes', () => {
    test.beforeEach(async ({ page }) => {
      // Mock default bootstrap
      await page.route('**/sdk/labels/bootstrap**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            namespaces: {
              login: {
                brand_tagline: "Control Center & Multi-tenant Administration",
                welcome_title: "Welcome back",
                welcome_body: "Access your administrative dashboard using enterprise credentials.",
                sso_action: "Sign in with Keycloak",
                sso_connecting: "Connecting...",
                divider_or: "or",
                local_action: "Local Admin Login",
                email_label: "Email",
                password_label: "Password",
                submit_action: "Sign In",
                submit_loading: "Signing in...",
                help_prompt: "Trouble signing in?",
                help_action: "Contact Support",
                error_invalid_credentials: "Invalid email or password.",
                error_authentication_failed: "Authentication could not be completed. Please try again.",
                error_generic: "Sign-in failed. Please try again or contact support."
              }
            },
            locale: 'en_US'
          })
        });
      });

      // Navigate to login page
      await page.goto('/login');
      // Wait for components to be ready
      await page.waitForLoadState('networkidle');

      // If local login form is collapsed, click to expand it so form fields are present in the DOM
      const localLoginBtn = page.locator('button:has-text("Local Admin Login")');
      if (await localLoginBtn.isVisible()) {
        await localLoginBtn.click();
      }
    });

    test('Login page - Light Mode', async ({ page }) => {
      // Ensure light mode
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'light');
        document.documentElement.classList.remove('dark');
      });
      
      // Check elements visibility
      await expect(page.locator('h2').first()).toContainText('Welcome back');
      await expect(page.locator('md-outlined-text-field').first()).toBeVisible();
      await expect(page.getByRole('button', { name: 'Sign In', exact: true })).toBeVisible();

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
      const submitButton = page.getByRole('button', { name: 'Sign In', exact: true });

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

  test.describe('Advanced Localization Tests', () => {
    test('English fallback when label bootstrap fails/timeouts', async ({ page }) => {
      await page.route('**/sdk/labels/bootstrap**', async (route) => {
        // Force request failure
        await route.abort('failed');
      });

      await page.goto('/login');
      
      // Should fall back to English copies from CATALOG_FALLBACK
      await expect(page.locator('h2').first()).toContainText('Welcome back');
      
      const localLoginBtn = page.locator('button:has-text("Local Admin Login")');
      await expect(localLoginBtn).toBeVisible();
      await localLoginBtn.click();

      // Check fields and help copies
      await expect(page.locator('md-outlined-text-field').first()).toHaveJSProperty('label', 'Email');
      await expect(page.locator('p:has-text("Trouble signing in?")')).toBeVisible();
    });

    test('Spanish copy when browser locale is es-* and bootstrap returns Spanish', async ({ browser }) => {
      const context = await browser.newContext({ locale: 'es-PE' });
      const page = await context.newPage();

      await page.route('**/sdk/labels/bootstrap**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            namespaces: {
              login: {
                welcome_title: "Bienvenido nuevamente",
                welcome_body: "Accede a tu panel administrativo usando credenciales empresariales.",
                local_action: "Acceso de administrador local",
                email_label: "Correo electronico",
                password_label: "Contrasena",
                submit_action: "Iniciar sesion",
                help_prompt: "Problemas para iniciar sesion?",
                help_action: "Contactar soporte"
              }
            },
            locale: 'es_PE'
          })
        });
      });

      await page.goto('/login');
      
      // Assert Spanish texts
      await expect(page.locator('h2').first()).toContainText('Bienvenido nuevamente');
      
      const localLoginBtn = page.locator('button:has-text("Acceso de administrador local")');
      await expect(localLoginBtn).toBeVisible();
      await localLoginBtn.click();

      await expect(page.locator('md-outlined-text-field').first()).toHaveJSProperty('label', 'Correo electronico');
      
      await context.close();
    });

    test('No locale selector and no [sys. text visible', async ({ page }) => {
      await page.goto('/login');
      
      // Ensure no select elements (locale selector) are visible
      await expect(page.locator('select')).not.toBeVisible();
      
      // Ensure no raw diagnostics [sys. are leaked to the user
      const content = await page.content();
      expect(content).not.toContain('[sys.');
    });

    test('Late hydration preserves interaction state', async ({ page }) => {
      let resolveRoute: () => void = () => {};
      const routePromise = new Promise<void>((resolve) => {
        resolveRoute = resolve;
      });

      await page.route('**/sdk/labels/bootstrap**', async (route) => {
        await routePromise;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            namespaces: {
              login: {
                welcome_title: "Welcome back (Hydrated)",
                local_action: "Local Admin Login (Hydrated)",
                email_label: "Email (Hydrated)",
                password_label: "Password (Hydrated)",
                help_prompt: "Trouble signing in? (Hydrated)"
              }
            },
            locale: 'en_US'
          })
        });
      });

      await page.goto('/login');

      // Expand form and type credentials while bootstrap is still pending
      const localLoginBtn = page.locator('button:has-text("Local Admin Login")');
      await localLoginBtn.click();

      const emailField = page.locator('md-outlined-text-field').first();
      const passwordField = page.locator('md-outlined-text-field').last();

      await emailField.click();
      await page.keyboard.type('test@example.com');

      await passwordField.click();
      await page.keyboard.type('secret123');

      // Trigger late hydration now
      resolveRoute();

      // Assert copy updates to hydrated labels
      await expect(page.locator('h2').first()).toContainText('Welcome back (Hydrated)');

      // Verify form is still expanded, values are preserved and no inputs got cleared
      const emailValue = await emailField.evaluate((el: any) => el.value);
      const passwordValue = await passwordField.evaluate((el: any) => el.value);

      expect(emailValue).toBe('test@example.com');
      expect(passwordValue).toBe('secret123');
    });
  });
});
