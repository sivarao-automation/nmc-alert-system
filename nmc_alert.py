import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "old.txt"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# --- 1. NMC Scraping ---
def scrap_nmc(driver):
    try:
        driver.get("https://www.nmc.org.in/all-news/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        rows = soup.find("table").find_all("tr")
        for row in rows[1:10]: # Top 10 items
            cols = row.find_all("td")
            if len(cols) >= 4:
                desc = cols[2].get_text(strip=True)
                date = cols[4].get_text(strip=True) if len(cols) > 4 else "N/A"
                news.append(f"🏥 *NMC UPDATE*\n📅 {date}\n📝 {desc}")
        return news
    except: return []

# --- 2. DME AP Scraping ---
def scrap_dme(driver):
    try:
        driver.get("https://dme.ap.nic.in/")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        # DME lo scrolling links (marquee) untayi
        links = soup.find_all("a", href=True)
        for l in links[:15]:
            title = l.get_text(strip=True)
            if len(title) > 20 and (".pdf" in l['href'] or "202" in title):
                news.append(f"🏛️ *DME AP UPDATE*\n📝 {title}")
        return news
    except: return []

# --- 3. MCC Scraping (UG, PG, SS) ---
def scrap_mcc(driver):
    urls = [
        "https://mcc.nic.in/ug-medical-counselling/",
        "https://mcc.nic.in/pg-medical-counselling/",
        "https://mcc.nic.in/super-speciality-counselling/"
    ]
    news = []
    for url in urls:
        try:
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # MCC News Section
            items = soup.select(".news-ticker a") or soup.find_all("a", {"class": "news-link"})
            category = "UG" if "ug-" in url else ("PG" if "pg-" in url else "SS")
            for item in items[:5]:
                title = item.get_text(strip=True)
                if title: news.append(f"🎓 *MCC {category} UPDATE*\n📝 {title}")
        except: continue
    return news

# --- 4. NTRUHS Scraping ---
def scrap_ntruhs(driver):
    try:
        driver.get("https://drntr.uhsap.in/index/")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        # NTRUHS 'What's New' leda table logic
        items = soup.find_all("a", href=True)
        for item in items:
            text = item.get_text(strip=True)
            if len(text) > 30 and ("202" in text or "Admission" in text or "Exam" in text):
                news.append(f"🩺 *NTRUHS UPDATE*\n📝 {text}")
        return news[:15]
    except: return []

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload, verify=False)

def main():
    print("--- Multi-Site Bot Active ---")
    driver = get_driver()
    all_news = []
    
    print("Checking NMC...")
    all_news.extend(scrap_nmc(driver))
    print("Checking DME...")
    all_news.extend(scrap_dme(driver))
    print("Checking MCC...")
    all_news.extend(scrap_mcc(driver))
    print("Checking NTRUHS...")
    all_news.extend(scrap_ntruhs(driver))
    
    driver.quit()

    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()
    else:
        old_news = []

    # Filter only new items
    new_items = [n for n in all_news if n.strip() not in old_news]

    if new_items:
        print(f"🚀 Found {len(new_items)} new updates!")
        for item in reversed(new_items):
            send_telegram_message(item)
            time.sleep(1)
        
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(all_news))
    else:
        print("😴 No new updates.")

if __name__ == "__main__":
    main()
