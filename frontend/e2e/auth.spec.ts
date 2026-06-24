import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  const randomSuffix = Math.floor(Math.random() * 1000000);
  const testEmail = `testuser${randomSuffix}@example.com`;
  const testUsername = `testuser${randomSuffix}`;
  const testPassword = 'Password123!';

  test('should register a new user successfully', async ({ page }) => {
    await page.goto('/');

    // Ensure we are on the landing page
    await expect(page.getByText('Chaatly')).toBeVisible();

    // Click "Get Started" to register
    await page.getByText('Get Started').click();

    // Register Email Step
    await expect(page.getByText('What\'s your email address?')).toBeVisible();
    await page.getByPlaceholder('you@example.com').fill(testEmail);
    await page.getByText('Continue').click();

    // Register Username Step
    await expect(page.getByText('Pick a username')).toBeVisible();
    await page.getByPlaceholder('e.g. spicylover99').fill(testUsername);
    await page.getByText('Continue').click();

    // Register Password Step
    await expect(page.getByText('Set a password')).toBeVisible();
    await page.getByPlaceholder('At least 8 characters').fill(testPassword);
    
    // Complete Sign Up
    await page.getByText('Complete Sign Up 🎉').click();

    // Wait for navigation to dashboard - Profile initial should be visible
    await expect(page.getByText(testUsername.charAt(0).toUpperCase(), { exact: true })).toBeVisible({ timeout: 15000 });
  });
});
