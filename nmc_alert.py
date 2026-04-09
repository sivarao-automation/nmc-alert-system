import requests
from bs4 import BeautifulSoup
import os
import urllib3

# SSL errors raakunda undadaniki
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://www.nmc.org.in/all-news/"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        # Website nundi data teeskuntundi
        r = requests.get(URL, headers=headers, timeout=25, verify=False)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        news_list = []
        # Table rows ni vethiki data teesthundi
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                date = cols[0].get_text(strip=True)
                title_cell = cols[1]
                title = title_cell.get_text(strip=True)
                link_tag = title_cell.find("a")
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else ""
                
                if title and title != "Subject":
                    # Telegram message format
                    news_list.append(f"📅 *Date:* {date}\n📝 *Title:* {title}\n🔗 [Click Here for Link]({link})")
        return news_list
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: BOT_TOKEN or CHAT_ID not found in Secrets!")
        return

    # Paatha news list ni check chesthundhi
    if os.path.exists("old.txt"):
        with open("old.txt", "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()
    else:
        old_news = []
    
    current_news = get_news()
    if not current_news:
        print("No news found or website down.")
        return

    # Kotha news matrame vethiki telegram ki pampisthundi
    new_items = [x for x in current_news if x not in old_news]
    
    if new_items:
        print(f"Found {len(new_items)} new updates!")
        for item in new_items:
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(telegram_url, data={
                "chat_id": CHAT_ID, 
                "text": item, 
                "parse_mode": "Markdown",
                "disable_web_page_preview": "false"
            })
        
        # Ippudu unna news ni old.txt lo save chesthundhi
        with open("old.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(current_news))
    else:
        print("No new updates found.")

if __name__ == "__main__":
    main()
