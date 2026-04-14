import streamlit as st
from playwright.sync_api import sync_playwright
import os
import time
import re

st.title("📸 Screenshot SaaS")

urls_input = st.text_area("URL 입력 (여러 개 가능)", height=200)

def clean_name(url):
    return re.sub(r'[^a-zA-Z0-9]', '_', url)

if st.button("캡처 시작"):
    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]

    os.makedirs("screenshots", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for url in urls:
            st.write(f"캡처 중: {url}")

            page = browser.new_page()
            page.goto(url)

            time.sleep(3)

            filename = clean_name(url) + ".png"
            path = f"screenshots/{filename}"

            page.screenshot(path=path, full_page=True)
            st.image(path)

        browser.close()