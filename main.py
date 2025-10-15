import requests
import time
import random
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# ==============================
# CONFIGURATION
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Kijiji RSS feed URL (Ontario, Cars & Trucks, your filters)
RSS_URL = "https://www.kijiji.ca/rss-srp/c174l9004?price=1000__15000&kilometres=1__260000&year=2010__2025&location=Ontario"

# Refresh interval in seconds
REFRESH_MIN = 30
REFRESH_MAX = 60

# ==============================
# FUNCTIONS
# ==============================

def send_telegram_message(text):
    """Send alert message via Telegram bot."""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ BOT_TOKEN or CHAT_ID not set!")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Alert sent")
        else:
            print(f"⚠️ Telegram API error: {response.status_code}, {response.text}")
    except Exception as e:
        print("⚠️ Exception sending Telegram message:", e)

def fetch_rss_listings():
    """Fetch listings from Kijiji RSS feed and parse price, year, km."""
    try:
        response = requests.get(RSS_URL, timeout=15)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall(".//item")
        results = []

        for item in items:
            title = item.findtext("title", default="N/A")
            link = item.findtext("link", default="N/A")
            description_html = item.findtext("description", default="")

            # Parse description HTML for price, year, km
            soup = BeautifulSoup(description_html, "html.parser")
            price = "N/A"
            year = "N/A"
            kms = "N/A"

            # Look for text patterns
            text = soup.get_text(separator="\n").split("\n")
            for line in text:
                line = line.strip()
                if line.lower().startswith("price"):
                    price = line.split(":")[-1].strip()
                elif line.lower().startswith("year"):
                    year = line.split(":")[-1].strip()
                elif line.lower().startswith("kilometres") or line.lower().startswith("km"):
                    kms = line.split(":")[-1].strip()

            results.append({
                "title": title,
                "link": link,
                "price": price,
                "year": year,
                "kms": kms
            })

        print(f"🔍 Found {len(results)} listings in RSS feed")
        return results

    except Exception as e:
        print("⚠️ Error fetching RSS:", e)
        return []

# ==============================
# MAIN LOOP
# ==============================

def main():
    print("🚗 Kijiji RSS bot started... watching for new listings!")
    seen = set()

    while True:
        listings = fetch_rss_listings()
        new_count = 0

        for listing in listings:
            if listing["link"] not in seen:
                seen.add(listing["link"])
                message = (
                    f"📢 NEW LISTING:\n"
                    f"{listing['title']}\n"
                    f"💰 Price: {listing['price']}\n"
                    f"📅 Year: {listing['year']}\n"
                    f"🏃 KMs: {listing['kms']}\n"
                    f"🔗 {listing['link']}"
                )
                send_telegram_message(message)
                new_count += 1

        print(f"🆕 {new_count} new listings processed")
        sleep_time = random.randint(REFRESH_MIN, REFRESH_MAX)
        print(f"⏱ Sleeping {sleep_time} seconds...\n")
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
