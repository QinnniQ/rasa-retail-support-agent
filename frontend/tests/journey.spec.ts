import { test, expect } from '@playwright/test'

test('missing item creates a real case and exposes order context', async ({ page, isMobile }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Waar kunnen we je/ })).toBeVisible()
  await expect(page.locator('.chat-top')).toContainText('Demo modus')
  if (process.env.CAPTURE_SCREENSHOTS)
    await page.screenshot({
      path: `../screenshots/home-${isMobile ? 'mobile' : 'desktop'}.png`,
      fullPage: true,
    })
  await page.getByRole('button', { name: /Ontbrekend artikel Een artikel/ }).click()
  await expect(page.getByText(/Wat is je voorbeeldordernummer/)).toBeVisible()
  await page.getByRole('button', { name: 'KV-10482', exact: true }).click()
  await expect(page.getByText(/Demonstratiecase #\d+ is aangemaakt/)).toBeVisible()
  await expect(page.locator('.order-items').getByText('Kruidvat dagcrème sensitive')).toBeVisible()
  if (isMobile) await page.getByRole('button', { name: 'Open menu' }).click()
  await page.getByRole('button', { name: 'Support Operations' }).click()
  await page
    .getByRole('textbox', { name: 'Operations toegangscode' })
    .fill('playwright-local-token')
  await page.getByRole('button', { name: 'Open werkruimte' }).click()
  await expect(
    page.getByRole('button', { name: /Case #\d+ · missing KV-10482/ }).first(),
  ).toBeVisible()
})

test('architecture shows configured demo mode', async ({ page, isMobile }) => {
  await page.goto('/')
  if (isMobile) await page.getByRole('button', { name: 'Open menu' }).click()
  await page.getByRole('button', { name: 'Architectuur', exact: true }).first().click()
  await expect(page.getByRole('heading', { name: 'Live servicestatus' })).toBeVisible()
  await expect(page.getByText('Niet geconfigureerd')).toBeVisible()
})
