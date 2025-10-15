import requests
from bs4 import BeautifulSoup
import time
import random
import os

# ==============================
# CONFIGURATION
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Kijiji search parameters
BASE_URL = "https://www.kijiji.ca/b-cars-trucks/ontario/c174l9004"
SEARCH_PARAMS = {
    "ad": "offering",
    "price": "1000__15000",
    "kilometres": "1__260000",
    "year": "2010__2025"
}

# Refresh interval (seconds)
REFRESH_MIN = 30
REFRESH_MAX = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/140.0.0.0 Safari/537.36"
}

# ==============================
# FUNCTIONS
# ==============================

def send_telegram_message(text):
    """Send alert message via Telegram bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("⚠️ Telegram send failed:", response.text)
    except Exception as e:
        print("⚠️ Telegram error:", e)

def fetch_listings():
    """Fetch and parse Kijiji listings based on filters."""
    try:
        response = requests.get(BASE_URL, params=SEARCH_PARAMS, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print("⚠️ Failed to fetch listings, status code:", response.status_code)
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.select(".search-item")
        results = []

        for item in listings:
            title_tag = item.select_one(".title")
            price_tag = item.select_one(".price")
            link_tag = item.select_one("a")
            detail_tags = item.select(".details li")
            
            year = detail_tags[0].get_text(strip=True) if len(detail_tags) > 0 else "N/A"
            kms = detail_tags[1].get_text(strip=True) if len(detail_tags) > 1 else "N/A"

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                price = price_tag.get_text(strip=True) if price_tag else "N/A"
                link = "https://www.kijiji.ca" + link_tag["href"]

                results.append({
                    "title": title,
                    "price": price,
                    "year": year,
                    "kms": kms,
                    "link": link
                })
        return results
    except Exception as e:
        print("⚠️ Fetch listings error:", e)
        return []

def main():
    print("🚗 Kijiji bot started... watching for new listings!")
    seen = set()

    while True:
        listings = fetch_listings()
        print(f"🔍 Found {len(listings)} listings")

        for listing in listings:
            if listing["link"] not in seen:
                seen.add(listing["link"])
                message = (
                    f"📢 NEW LISTING:\n{listing['title']}\n"
                    f"💰 {listing['price']}\n"
                    f"📅 {listing['year']}\n"
                    f"🏃 {listing['kms']}\n"
                    f"🔗 {listing['link']}"
                )
                send_telegram_message(message)
                print(f"✅ Sent alert: {listing['title']}")

        sleep_time = random.randint(REFRESH_MIN, REFRESH_MAX)
        print(f"⏱ Sleeping {sleep_time} seconds...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    main()
