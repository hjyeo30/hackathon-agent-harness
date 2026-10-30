const { test, expect } = require('@playwright/test');
const fs = require('node:fs/promises');

test('real upload, independent 10% oracle, date filter, and downloaded contents', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('CSV 파일').setInputFiles('fixtures/unequal-batches.csv');
  const response = page.waitForResponse(r => r.url().endsWith('/api/analyze'));
  await page.getByRole('button', { name: '분석', exact: true }).click();
  expect((await (await response).json()).yield_rate).toBeCloseTo(0.1);
  await expect(page.getByTestId('yield-rate')).toHaveText('10.00%');
  await expect(page.locator('#rows tr')).toHaveCount(2);

  await page.getByLabel('종료일').fill('2026-10-01');
  await expect(page.getByRole('button', { name: 'CSV 다운로드' })).toBeDisabled();
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('90.00%');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'CSV 다운로드' }).click();
  const download = await downloadPromise;
  const csv = await fs.readFile(await download.path(), 'utf8');
  expect(csv).toContain('A,E1,2026-10-01,9,10');
  expect(csv).not.toContain('B,E1');
  expect(csv.trim().split(/\r?\n/)).toHaveLength(2);
});

test('equipment filter and empty result preserve meaning', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('CSV 파일').setInputFiles('fixtures/multi-equipment.csv');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('분석 완료');
  await page.getByLabel('설비', { exact: true }).selectOption('E2');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('100.00%');
  await expect(page.locator('#rows tr')).toHaveCount(1);
  await page.getByLabel('시작일').fill('2026-11-01');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('데이터 없음');
  await expect(page.locator('#rows tr')).toHaveCount(0);
});

test('invalid counts fail visibly and clear previous success', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('CSV 파일').setInputFiles('fixtures/unequal-batches.csv');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('10.00%');
  await page.getByLabel('CSV 파일').setInputFiles({
    name: 'invalid.csv', mimeType: 'text/csv',
    buffer: Buffer.from('batch,equipment,date,good,total\nA,E1,2026-10-01,11,10\n'),
  });
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('0 <= good <= total');
  await expect(page.getByTestId('yield-rate')).toHaveText('—');
  await expect(page.getByRole('button', { name: 'CSV 다운로드' })).toBeDisabled();
});

test('replacing the CSV resets an equipment filter absent from the new file', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('CSV 파일').setInputFiles('fixtures/multi-equipment.csv');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByRole('status')).toHaveText('분석 완료');
  await page.getByLabel('설비', { exact: true }).selectOption('E2');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('100.00%');
  await page.getByLabel('CSV 파일').setInputFiles({
    name: 'only-e1.csv', mimeType: 'text/csv',
    buffer: Buffer.from('batch,equipment,date,good,total\nZ,E1,2026-10-01,9,10\n'),
  });
  await expect(page.getByLabel('설비', { exact: true })).toHaveValue('');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('90.00%');
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'CSV 다운로드' }).click();
  const csv = await fs.readFile(await (await downloadPromise).path(), 'utf8');
  expect(csv).toContain('Z,E1,2026-10-01,9,10');
});

test('a slow older response cannot overwrite the latest filter', async ({ page }) => {
  // Force transport completion even if cancellation is ineffective. The request
  // ownership guard must still protect the visible result.
  await page.addInitScript(() => {
    const fetchOriginal = window.fetch;
    window.fetch = (input, init = {}) => fetchOriginal(input, { ...init, signal: undefined });
  });
  let releaseFirst;
  const gate = new Promise(resolve => { releaseFirst = resolve; });
  let firstReceived;
  const firstReady = new Promise(resolve => { firstReceived = resolve; });
  let count = 0;
  // Only delivery timing is controlled. The server still computes both answers.
  await page.route('**/api/analyze', async route => {
    const index = ++count;
    const response = await route.fetch();
    if (index === 1) { firstReceived(); await gate; }
    await route.fulfill({ response });
  });
  await page.goto('/');
  await page.getByLabel('CSV 파일').setInputFiles('fixtures/unequal-batches.csv');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await firstReady;
  await page.getByLabel('종료일').fill('2026-10-01');
  await page.getByRole('button', { name: '분석', exact: true }).click();
  await expect(page.getByTestId('yield-rate')).toHaveText('90.00%');
  const oldResponse = page.waitForResponse(response =>
    response.url().endsWith('/api/analyze') &&
    response.request().postDataJSON().filters.end === ''
  );
  releaseFirst();
  await (await oldResponse).finished();
  // Let the delivered response's promise callbacks finish, without a timed sleep.
  await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 0)));
  await expect(page.locator('#rows tr')).toHaveCount(1);
  await expect(page.getByTestId('yield-rate')).toHaveText('90.00%');
});
