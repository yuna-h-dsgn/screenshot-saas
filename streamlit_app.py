import os

# 🔥 Cloud 환경에서 Playwright 브라우저 자동 설치
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

import streamlit as st
from playwright.sync_api import sync_playwright
import time
import re
from urllib.parse import urlparse

st.set_page_config(page_title="Screenshot SaaS", layout="wide")

st.title("📸 Screenshot SaaS")
st.caption("여러 웹사이트를 한 번에 캡처합니다")

urls_input = st.text_area(
    "URL 입력 (줄바꿈으로 여러 개 입력)",
    height=200,
    placeholder="https://example.com\nhttps://google.com"
)

# ✅ 사이트 이름 추출 (파일명용)
def get_site_name(url):
    try:
        domain = urlparse(url).netloc
        domain = domain.replace("www.", "")
        name = domain.split(".")[0]
        return re.sub(r'[^a-zA-Z0-9]', '', name)
    except:
        return "screenshot"

# 팝업 제거
def close_popups(page):
    texts = ["accept", "agree", "got it", "close", "확인", "동의"]
    for text in texts:
        try:
            page.locator(f"text={text}").first.click(timeout=1000)
        except:
            pass

    try:
        page.keyboard.press("Escape")
    except:
        pass

# 자동 스크롤
def auto_scroll(page):
    try:
        page.evaluate("""
        async () => {
            await new Promise(resolve => {
                let totalHeight = 0;
                let distance = 500;
                let timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
        """)
    except:
        pass

# 캡처 함수
def capture_urls(urls):
    results = []
    os.makedirs("screenshots", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        for i, url in enumerate(urls):
            try:
                page = browser.new_page(
                    viewport={"width": 1920, "height": 1080}
                )

                page.goto(url, timeout=60000)

                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except:
                    pass

                time.sleep(2)

                close_popups(page)
                auto_scroll(page)

                time.sleep(1)

                # ✅ 사이트명 + 순번으로 파일명 생성
                filename = f"{get_site_name(url)}_{i+1}.png"
                path = f"screenshots/{filename}"

                page.screenshot(path=path, full_page=True)
                page.close()

                results.append((url, path))

            except Exception:
                results.append((url, None))

        browser.close()

    return results


# 버튼 실행
if st.button("🚀 캡처 시작"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

    if not urls:
        st.warning("URL을 입력해주세요")
    else:
        progress = st.progress(0)
        status = st.empty()

        for i, url in enumerate(urls):
            status.text(f"[{i+1}/{len(urls)}] 준비 중: {url}")
            progress.progress(i / len(urls))

        results = capture_urls(urls)

        progress.progress(1.0)
        status.text("✅ 완료!")

        st.divider()

        for url, path in results:
            st.subheader(url)

            if path and os.path.exists(path):
                st.image(path)

                with open(path, "rb") as f:
                    st.download_button(
                        label="📥 다운로드",
                        data=f,
                        file_name=os.path.basename(path),
                        mime="image/png"
                    )
            else:
                st.error("캡처 실패")