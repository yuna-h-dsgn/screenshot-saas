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


def capture(page, url, filename):
    # ✅ 핵심: networkidle 제거
    page.goto(url, wait_until="domcontentloaded", timeout=20000)

    # ✅ 렌더링 안정화
    page.wait_for_timeout(2000)

    # ✅ lazy load 강제
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)

    # ✅ 고화질 캡처
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
            device_scale_factor=2  # 🔥 화질 핵심
        )

        for url in urls:
            page = context.new_page()
            filename = f"{clean_filename(url)}.png"

            try:
                capture(page, url, filename)
                results.append((url, filename, "캡처 성공 ✅"))

            except Exception as e:
                results.append((url, None, f"실패 ❌: {str(e)}"))

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