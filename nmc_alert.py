import cloudscraper
import requests
from bs4 import BeautifulSoup
import os
import time
import urllib3
from requests.adapters import HTTPAdapter

# GitHub environment compatibility kosam idi simplify chesam
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
URL = "https://www.nmc.org.in/all-news/"
BOT_TOKEN = os.getenv("BOT_TOKEN") 
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "old.txt"

# SSL Bypass Adapter
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

def get_news():
    scraper = cloudscraper.create_scraper()
    scraper.mount("https://", SSLAdapter())
    
    try:
        print("🔍 Website fetch start...")
        r = scraper.get(URL, timeout=30, verify=False)
        
        if r.status_code != 200:
            print(f"❌ Status Code: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        news_list = []
        rows = soup.find_all("tr")
        
        if not rows:
            print("❌ No rows found.")
            return []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                date = cols[0].get_text(strip=True)
                title_cell = cols[1]
                title = title_cell.get_text(strip=True)
                
                if title.lower() == "subject" or date.lower() == "date":
                    continue

                link_tag = title_cell.find("a")
                link = ""
                if link_tag and link_tag.get('href'):
                    link = link_tag['href']
                    if not link.startswith('http'):
                        link = "https://www.nmc.org.in" + link
                
                if title:
                    news_list.append(f"📅 *Date:* {date}\n📝 *Title:* {title}\n🔗 [Click Here]({link})")
        
        print(f"✅ Found {len(news_list)} items.")
        return news_list
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(telegram_url, data=payload, verify=False)
        return r.status_code == 200
    except:
        return False

def main():
    print("--- NMC Bot Active ---")
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Secrets Missing!")
        return

    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()
    else:
        old_news = []

    current_news = get_news()
    if not current_news:
        print("⚠️ No data.")
        return

    def get_title(item):
        lines = item.split('\n')
        return lines[1] if len(lines) > 1 else item

    old_titles = [get_title(o) for o in old_news]
    new_items = [item for item in current_news if get_title(item) not in old_titles]

    if new_items:
        print(f"🚀 Sending {len(new_items)} updates...")
        for item in reversed(new_items):
            send_telegram_message(item)
            time.sleep(1)
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(current_news))
    else:
        print("😴 No new updates.")

if __name__ == "__main__":
    main()
