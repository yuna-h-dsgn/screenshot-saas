import streamlit as st
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import re
import time
import os

st.set_page_config(page_title="Screenshot SaaS", layout="wide")

st.title("📸 Screenshot SaaS")
st.write("여러 웹사이트를 한 번에 캡처합니다")

urls_input = st.text_area("URL 입력 (줄바꿈으로 여러 개 입력)", height=150)

def clean_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    domain = re.sub(r'[^\w\-_\.]', '_', domain)
    return domain

def fast_capture(page, url, filename):
    page.goto(url, wait_until="domcontentloaded", timeout=15000)
    time.sleep(1)

    page.screenshot(
        path=filename,
        full_page=True,
        type="jpeg",
        quality=70
    )

def high_quality_capture(page, url, filename):
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)

    page.screenshot(
        path=filename,
        full_page=True,
        type="png"
    )

def capture_urls(urls):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            device_scale_factor=2  # 🔥 핵심 (고화질)
        )

        for url in urls:
            page = context.new_page()
            filename = f"{clean_filename(url)}.png"

            try:
                # 🚀 1차 빠른 시도
                fast_capture(page, url, filename)
                results.append((url, filename, "빠른 캡처 성공 ⚡"))

            except Exception as e:
                try:
                    # 🔥 실패하면 고품질 재시도
                    high_quality_capture(page, url, filename)
                    results.append((url, filename, "고품질 재시도 성공 🎯"))

                except Exception as e2:
                    results.append((url, None, f"완전 실패 ❌: {str(e2)}"))

            page.close()

        browser.close()

    return results

if st.button("🚀 캡처 시작"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

    if not urls:
        st.warning("URL을 입력하세요")
    else:
        with st.spinner("캡처 진행 중..."):
            results = capture_urls(urls)

        st.success("완료!")

        for url, file, status in results:
            st.markdown(f"### {url}")
            st.write(status)

            if file and os.path.exists(file):
                st.image(file)