import asyncio, sys
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={'width':390,'height':844}, color_scheme='light', device_scale_factor=1)
        page = await ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto('http://127.0.0.1:8867/index.html', wait_until='domcontentloaded')
        await page.wait_for_selector('.lot-card', timeout=15000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path='/opt/data/home/portal-dominicano/screenshots/top_light.png')
        for _ in range(20):
            await page.mouse.wheel(0, 1200)
            await page.wait_for_timeout(300)
        await page.wait_for_timeout(2000)
        await page.screenshot(path='/opt/data/home/portal-dominicano/screenshots/full_light.png', full_page=True)
        states = await page.evaluate("""() => {
          const ids = ['loteria-grid','mlb-grid','weather-grid','noticias-list','tendencias-list','divisas-grid','economia-grid','eventos-grid'];
          const r = {};
          ids.forEach(id => {
            const el = document.getElementById(id);
            r[id] = el ? (el.innerText || '').slice(0, 40) : 'MISSING';
          });
          return r;
        }""")
        print('=== SECTION STATES (light/mobile) ===')
        for k,v in states.items():
            print(f'  {k}: {v!r}')
        mn = await page.evaluate("() => ({panel: !!document.getElementById('mn1'), cards: document.querySelectorAll('.lot-card').length, fechas: document.querySelectorAll('.lot-fecha').length, dias: document.querySelectorAll('.lot-dia').length, balls: document.querySelectorAll('.ball').length})")
        print('=== MIS NUMEROS / FECHA ===')
        print(mn)
        await page.fill('#mn1', '11'); await page.fill('#mn2', '22'); await page.fill('#mn3', '33')
        await page.click('#mnGo')
        await page.wait_for_timeout(500)
        res = await page.evaluate("() => ({result: document.getElementById('mnResult').innerText, matches: document.querySelectorAll('.lot-card.match').length})")
        print('=== MIS NUMEROS RESULT ===')
        print(res)
        await ctx.close()

        ctx2 = await browser.new_context(viewport={'width':390,'height':844}, color_scheme='dark')
        page2 = await ctx2.new_page()
        await page2.goto('http://127.0.0.1:8867/index.html', wait_until='domcontentloaded')
        await page2.wait_for_selector('.lot-card', timeout=15000)
        await page2.wait_for_timeout(1200)
        await page2.screenshot(path='/opt/data/home/portal-dominicano/screenshots/top_dark.png')
        bg = await page2.evaluate("() => getComputedStyle(document.body).backgroundColor")
        print('=== DARK MODE ===')
        print('body bg:', bg)
        await ctx2.close()

        print('PAGEERRORS:', errors if errors else 'none')
        await browser.close()

asyncio.run(main())
