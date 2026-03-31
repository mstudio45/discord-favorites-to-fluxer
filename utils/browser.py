from playwright.async_api import async_playwright

_playwright = None
_browser = None

async def get_browser():
    global _playwright, _browser

    if _playwright is None:
        _playwright = await async_playwright().start()
    
    if _browser is None:
        _browser = await _playwright.chromium.launch(headless=True)

    return _browser

async def close_browser():
    global _playwright, _browser

    if _browser is not None:
        await _browser.close()
        _browser = None

    if _playwright is not None:
        await _playwright.stop()
        _playwright = None