import cloudscraper
import requests
from bs4 import BeautifulSoup
import os
import time
import urllib3
from requests.adapters import HTTPAdapter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
URL = "https://www.nmc.org.in/all-news/"
BOT_TOKEN = os.getenv("BOT_TOKEN") 
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "old.txt"

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
        print("🔍 NMC Website check chestunnanu...")
        r = scraper.get(URL, timeout=30, verify=False)
        
        if r.status_code != 200:
            print(f"❌ Connection Error: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        news_list = []
        
        # Table vethukutunnam
        table = soup.find("table")
        if not table:
            print("❌ Table dhorakaledhu! Website layout check cheyali.")
            return []

        rows = table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            
            # Screenshot prakaram 5 columns unnayi
            if len(cols) >= 4:
                # Description column (Index 2)
                description = cols[2].get_text(strip=True)
                # Published On column (Index 4)
                published_on = cols[4].get_text(strip=True) if len(cols) > 4 else "N/A"
                
                # Header row ni skip cheyadaniki
                if "description" in description.lower() or "sl no" in description.lower():
                    continue

                # Download link (Index 3)
                link_tag = cols[3].find("a")
                link = ""
                if link_tag and link_tag.get('href'):
                    link = link_tag['href']
                    if not link.startswith('http'):
                        link = "https://www.nmc.org.in" + link
                
                if description:
                    message = f"📅 *Published:* {published_on}\n📝 *Update:* {description}\n🔗 [Download Document]({link})"
                    news_list.append(message)
        
        print(f"✅ Mottam {len(news_list)} news items dhorikaayi.")
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
        print("❌ Secrets Missing! GitHub settings check cheyandi.")
        return

    # Paatha data load cheyadam
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()
    else:
        old_news = []

    current_news = get_news()
    if not current_news:
        return

    # Kotha updates filter (Title match logic)
    def get_desc(item):
        # Update line ni extract chestundi comparison kosam
        lines = item.split('\n')
        return lines[1] if len(lines) > 1 else item

    old_titles = [get_desc(o) for o in old_news if o.strip()]
    new_items = [item for item in current_news if get_desc(item) not in old_titles]

    if new_items:
        print(f"🚀 {len(new_items)} kotha updates dhorikaayi!")
        for item in reversed(new_items):
            if send_telegram_message(item):
                print("📤 Telegram ki pampaanu.")
            time.sleep(1)
        
        # old.txt update
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(current_news))
    else:
        print("😴 Kotha updates emi levu.")

if __name__ == "__main__":
    main()
