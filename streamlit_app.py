import os

if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    os.system("playwright install chromium")

import streamlit as st
from playwright.sync_api import sync_playwright
import time
from urllib.parse import urlparse
from PIL import Image

st.set_page_config(page_title="Screenshot SaaS", layout="wide")

st.title("📸 Screenshot SaaS")
st.caption("빠른 캡처 + 무거운 사이트 대응")

urls_input = st.text_area("URL 입력", height=200)

def get_site_name(url):
    return urlparse(url).netloc.replace("www.", "").split(".")[0]

# 🔥 분할 캡처
def scroll_capture(page, path):
    total_height = page.evaluate("document.body.scrollHeight")
    viewport_height = page.viewport_size["height"]

    screenshots = []
    y = 0
    index = 0

    while y < total_height:
        page.evaluate(f"window.scrollTo(0, {y})")
        time.sleep(0.8)

        file = f"{path}_{index}.png"
        page.screenshot(path=file)
        screenshots.append(file)

        y += viewport_height
        index += 1

    images = [Image.open(img) for img in screenshots]

    total_width = images[0].width
    total_height = sum(img.height for img in images)

    final_image = Image.new("RGB", (total_width, total_height))

    y_offset = 0
    for img in images:
        final_image.paste(img, (0, y_offset))
        y_offset += img.height

    final_image.save(path)

    for img in screenshots:
        os.remove(img)

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
            ]
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )

        for i, url in enumerate(urls):
            try:
                st.info(f"🔄 {url}")

                page = context.new_page()

                page.goto(url, timeout=60000, wait_until="domcontentloaded")

                time.sleep(2)

                filename = f"screenshots/{get_site_name(url)}_{i+1}.png"

                # 🔥 1차: 빠른 full_page 시도
                try:
                    page.screenshot(path=filename, full_page=True)
                    st.success(f"⚡ 빠른 캡처 성공")

                except Exception as fast_error:
                    st.warning(f"⚠️ fallback: 분할 캡처 전환")

                    # 🔥 lazy load 처리
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(2)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(1)

                    # 🔥 2차: 분할 캡처
                    scroll_capture(page, filename)
                    st.success(f"🐢 분할 캡처 성공")

                page.close()
                results.append((url, filename))

            except Exception as e:
                results.append((url, None))
                st.error(f"❌ 실패: {e}")

        browser.close()

    return results


if st.button("🚀 시작"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

    results = capture(urls)

    st.divider()

    for url, path in results:
        st.subheader(url)
        if path and os.path.exists(path):
            st.image(path)
        else:
            st.error("캡처 실패")