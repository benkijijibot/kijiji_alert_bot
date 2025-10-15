import asyncio
from playwright.async_api import async_playwright
import requests
import os
import time
import random

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

BASE_URL = "https://www.kijiji.ca/b-cars-trucks/ontario/c174l9004"
SEARCH_PARAMS = "?ad=offering&price=1000__15000&kilometres=1__260000&year=2010__2025"

REFRESH_MIN = 30
REFRESH_MAX = 60

seen_links = set()

# ==============================
# FUNCTIONS
# ==============================

def send_telegram(text):
    if BOT_TOKEN is None or CHAT_ID is None:
        print("⚠️ BOT_TOKEN or CHAT_ID not set!")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        resp = requests.post(url, data=data)
        if resp.status_code == 200:
            print(f"✅ Telegram message sent: {text.splitlines()[0]}")
        else:
            print(f"⚠️ Telegram failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# ==============================
# MAIN SCRAPER
# ==============================

async def scrape_kijiji():
    global seen_links
    print("🚀 Script started")
    print("🔑 Environment loaded:", "BOT_TOKEN set" if BOT_TOKEN else "BOT_TOKEN missing",
          "| CHAT_ID set" if CHAT_ID else "CHAT_ID missing")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            print("🌐 Browser launched successfully")
        except Exception as e:
            print("⚠️ Failed to launch browser:", e)
            return

        while True:
            try:
                print("🔍 Fetching Kijiji listings...")
                await page.goto(BASE_URL + SEARCH_PARAMS, timeout=60000)
                await page.wait_for_timeout(5000)

                listings = await page.query_selector_all("div.search-item")
                print(f"📝 Found {len(listings)} listings on page")

                for item in listings:
                    title_tag = await item.query_selector(".title")
                    price_tag = await item.query_selector(".price")
                    link_tag = await item.query_selector("a")
                    details = await item.query_selector_all(".details li")

                    if not (title_tag and link_tag):
                        continue

                    title = (await title_tag.inner_text()).strip()
                    price = (await price_tag.inner_text()).strip() if price_tag else "N/A"
                    link = "https://www.kijiji.ca" + (await link_tag.get_attribute("href"))
                    year = await details[0].inner_text() if len(details) > 0 else "N/A"
                    kms = await details[1].inner_text() if len(details) > 1 else "N/A"

                    if link not in seen_links:
                        seen_links.add(link)
                        message = f"📢 NEW LISTING:\n{title}\n💰 {price}\n📅 {year}\n🏃 {kms}\n🔗 {link}"
                        send_telegram(message)

                sleep_time = random.randint(REFRESH_MIN, REFRESH_MAX)
                print(f"⏱ Sleeping {sleep_time}s...\n")
                await asyncio.sleep(sleep_time)

            except Exception as e:
                print(f"⚠️ Scraper error: {e}")
                await asyncio.sleep(30)

        await browser.close()

# ==============================
# ENTRY POINT
# ==============================

if __name__ == "__main__":
    asyncio.run(scrape_kijiji())
