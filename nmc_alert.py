import cloudscraper
import requests
from bs4 import BeautifulSoup
import os
import time
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

# SSL warnings ni silent cheyadaniki
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
URL = "https://www.nmc.org.in/all-news/"
# Secrets (Variables set cheyakapothe ikkada direct ga quotes lo ivvandi)
BOT_TOKEN = os.getenv("BOT_TOKEN") 
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "old.txt"

# SSL Error ni bypass chese special class
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.check_hostname = False
        context.verify_mode = urllib3.util.ssl_.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)

def get_news():
    scraper = cloudscraper.create_scraper()
    # Adapter ni mount chestunnam SSL bypass kosam
    scraper.mount("https://", SSLAdapter())
    
    try:
        print("🔍 Website nundi data fetch chestunnanu (Advanced SSL Bypass)...")
        r = scraper.get(URL, timeout=30, verify=False)
        
        if r.status_code != 200:
            print(f"❌ Website Error! Status Code: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        news_list = []
        
        # Table rows vethukudham
        rows = soup.find_all("tr")
        
        if not rows:
            print("❌ Rows dhorakaledhu! Website layout check cheyali.")
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
        
        print(f"✅ Total {len(news_list)} items dhorikaayi.")
        return news_list

    except Exception as e:
        print(f"❌ Scraping Error: {e}")
        return []

def send_telegram_message(message):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    
    try:
        # Telegram ki simple requests saripotundi
        r = requests.post(telegram_url, data=payload, verify=False)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Telegram Error: {e}")
        return False

def main():
    print("--- NMC Bot Active ---")
    
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ BOT_TOKEN leda CHAT_ID missing! Secrets check cheyandi.")
        return

    # Paatha news load
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()
    else:
        old_news = []

    current_news = get_news()
    
    if not current_news:
        print("⚠️ Data emi dhorakaledhu.")
        return

    # Kotha news filter
    def get_title(item):
        lines = item.split('\n')
        return lines[1] if len(lines) > 1 else item

    old_titles = [get_title(o) for o in old_news]
    new_items = [item for item in current_news if get_title(item) not in old_titles]

    if new_items:
        print(f"🚀 {len(new_items)} kotha updates pampistunnanu!")
        for item in reversed(new_items):
            if send_telegram_message(item):
                print("📤 Sent to Telegram.")
            time.sleep(1)

        # old.txt update
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(current_news))
    else:
        print("😴 Kotha updates emi levu.")

if __name__ == "__main__":
    main()
