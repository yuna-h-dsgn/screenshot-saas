from playwright.sync_api import sync_playwright
import time
import os

URLS = [
    "https://framacph.com/collections/shop",
    "https://mokevalley.co.nz/gallery",
    "https://destroyer.la/",
    "https://www.ssense.com/ko-kr/editorial/culture/fashion-internet-history",
    "https://signal-a.studio/",
    "https://bergerfohr.com/art",
    "https://advance-copy.com/",
    "https://paulcalver.cc/"
]

OUTPUT_DIR = "screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_wait(page):
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except:
        pass
    time.sleep(4)

def remove_popups(page):
    selectors = [
        "button:has-text('Accept')",
        "button:has-text('Agree')",
        "button:has-text('OK')",
        "button:has-text('닫기')",
        "[aria-label='close']",
        "[data-testid='close']",
        ".close",
        ".popup-close"
    ]
    for sel in selectors:
        try:
            page.locator(sel).first.click(timeout=2000)
        except:
            pass

def auto_scroll(page):
    page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                let distance = 500;
                let timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 300);
            });
        }
    """)

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = browser.new_page(
            viewport={"width": 1920, "height": 1080}
        )

        for i, url in enumerate(URLS):
            print(f"📸 {i+1}/{len(URLS)} 캡처 중: {url}")

            try:
                page.goto(url, timeout=60000)

                safe_wait(page)

                remove_popups(page)

                auto_scroll(page)
                time.sleep(2)

                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)

                page.screenshot(
                    path=f"{OUTPUT_DIR}/site_{i+1}.png",
                    full_page=True
                )

                print("✅ 완료")

            except Exception as e:
                print(f"❌ 실패: {url}")
                print(e)

        browser.close()

if __name__ == "__main__":
    capture()