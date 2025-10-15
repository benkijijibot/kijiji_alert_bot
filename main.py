import requests
import xml.etree.ElementTree as ET
import os
import time
import random

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Kijiji RSS feed for Ontario cars & trucks with filters
# price: 1000–15000, km: 1–260000, year: 2010–2025
RSS_URL = (
    "https://www.kijiji.ca/rss-srp/c174l9004?price=1000__15000"
    "&kilometres=1__260000&year=2010__2025&location=Ontario"
)

# Refresh interval (seconds)
REFRESH_MIN = 30
REFRESH_MAX = 60

seen_links = set()

# ==============================
# FUNCTIONS
# ==============================

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ BOT_TOKEN or CHAT_ID not set!")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        resp = requests.post(url, data={"chat_id": CHAT_ID, "text": text})
        if resp.status_code == 200:
            print(f"✅ Alert sent: {text.splitlines()[0]}")
        else:
            print(f"⚠️ Telegram failed ({resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

def fetch_listings():
    try:
        resp = requests.get(RSS_URL)
        root = ET.fromstring(resp.content)
        listings = []

        for item in root.findall(".//item"):
            title = item.find("title").text
            link = item.find("link").text
            description = item.find("description").text or ""

            # extract price, year, kms from description
            price = "N/A"
            year = "N/A"
            kms = "N/A"

            if "Price:" in description:
                price = description.split("Price:")[1].split("<")[0].strip()
            if "Year:" in description:
                year = description.split("Year:")[1].split("<")[0].strip()
            if "Kms:" in description:
                kms = description.split("Kms:")[1].split("<")[0].strip()

            listings.append({
                "title": title,
                "link": link,
                "price": price,
                "year": year,
                "kms": kms
            })
        return listings
    except Exception as e:
        print(f"⚠️ RSS fetch error: {e}")
        return []

def main():
    print("🚗 Kijiji RSS bot started")
    global seen_links

    while True:
        listings = fetch_listings()

        for listing in listings:
            if listing["link"] not in seen_links:
                seen_links.add(listing["link"])
                message = (
                    f"📢 NEW LISTING:\n{listing['title']}\n"
                    f"💰 {listing['price']}\n"
                    f"📅 {listing['year']}\n"
                    f"🏃 {listing['kms']}\n"
                    f"🔗 {listing['link']}"
                )
                send_telegram(message)

        sleep_time = random.randint(REFRESH_MIN, REFRESH_MAX)
        print(f"⏱ Sleeping {sleep_time}s...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
