import os

# 🔥 Playwright 브라우저 설치 (Streamlit Cloud 대응)
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

import streamlit as st
from playwright.sync_api import sync_playwright
import time
from urllib.parse import urlparse
from PIL import Image

st.set_page_config(page_title="Screenshot SaaS", layout="wide")

st.title("📸 Screenshot SaaS")
st.caption("빠른 캡처 + 무거운 사이트 완벽 대응")

urls_input = st.text_area("URL 입력 (줄바꿈으로 여러 개)", height=200)

def get_site_name(url):
    try:
        return urlparse(url).netloc.replace("www.", "").split(".")[0]
    except:
        return "site"

# 🔥 분할 캡처 (fallback)
def scroll_capture(page, path):
    total_height = page.evaluate("document.body.scrollHeight")
    viewport_height = page.viewport_size["height"]

    screenshots = []
    y = 0
    index = 0

    while y < total_height:
        page.evaluate(f"window.scrollTo(0, {y})")
        time.sleep(0.8)

        temp_file = f"{path}_{index}.png"
        page.screenshot(path=temp_file)
        screenshots.append(temp_file)

        y += viewport_height
        index += 1

    # 🔥 이미지 합치기
    images = [Image.open(img) for img in screenshots]

    total_width = images[0].width
    total_height = sum(img.height for img in images)

    final_image = Image.new("RGB", (total_width, total_height))

    y_offset = 0
    for img in images:
        final_image.paste(img, (0, y_offset))
        y_offset += img.height

    final_image.save(path)

    # 임시 파일 삭제
    for img in screenshots:
        os.remove(img)

# 🔥 메인 캡처
def capture(urls):
    results = []
    os.makedirs("screenshots", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--no-zygote",
                "--single-process",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--metrics-recording-only",
                "--mute-audio",
            ]
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
            user_agent="Mozilla/5.0"
        )

        for i, url in enumerate(urls):
            try:
                st.info(f"🔄 처리 중: {url}")

                page = context.new_page()

                # 🔥 안정적인 로딩
                page.goto(url, timeout=60000, wait_until="domcontentloaded")

                time.sleep(2)

                filename = f"screenshots/{get_site_name(url)}_{i+1}.png"

                # ⚡ 1차: 빠른 full 캡처
                try:
                    page.screenshot(path=filename, full_page=True)
                    st.success("⚡ 빠른 캡처 성공")

                except Exception as fast_error:
                    st.warning("⚠️ fallback: 분할 캡처 실행")

                    # lazy load 강제
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(1)

                    # 🐢 2차: 분할 캡처
                    scroll_capture(page, filename)
                    st.success("🐢 분할 캡처 성공")

                page.close()
                results.append((url, filename))

            except Exception as e:
                results.append((url, None))
                st.error(f"❌ 실패: {url} → {e}")

        browser.close()

    return results


# 실행
if st.button("🚀 캡처 시작"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

    if not urls:
        st.warning("URL을 입력해주세요")
    else:
        results = capture(urls)

        st.divider()

        for url, path in results:
            st.subheader(url)

            if path and os.path.exists(path):
                st.image(path)
            else:
                st.error("캡처 실패")