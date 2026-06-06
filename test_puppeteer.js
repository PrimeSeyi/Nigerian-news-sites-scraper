const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();
  try {
    const response = await page.goto('http://40.87.97.49', { waitUntil: 'networkidle2', timeout: 10000 });
    console.log('Status:', response.status());
    console.log('Title:', await page.title());
  } catch (e) {
    console.error('Navigation failed:', e.message);
  }
  await browser.close();
})();
