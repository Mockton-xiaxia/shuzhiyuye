const { chromium } = require('playwright');

async function main() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // 访问登录页
  console.log('访问登录页...');
  await page.goto('http://60.165.239.173:9000/fishery-web/#/login');
  await page.waitForTimeout(2000);
  
  // 截图
  await page.screenshot({ path: 'D:\\ai\\domo\\yuye\\crawl_output\\screenshots\\01-login.png', fullPage: true });
  console.log('已保存登录页截图');
  
  await browser.close();
}

main().catch(console.error);
