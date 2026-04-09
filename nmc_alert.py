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

# Settings - Ivi automatic ga GitHub nundi tiskuntundi
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "old.txt"

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Browser kanipinchakunda run avtundi
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# --- 1. NMC Scraping Logic ---
def scrap_nmc(driver):
    try:
        driver.get("https://www.nmc.org.in/all-news/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        rows = soup.find("table").find_all("tr")
        for row in rows[1:15]:
            cols = row.find_all("td")
            if len(cols) >= 4:
                desc = cols[2].get_text(strip=True)
                date = cols[4].get_text(strip=True) if len(cols) > 4 else "N/A"
                news.append(f"🏥 *NMC UPDATE*\n📅 {date}\n📝 {desc}")
        return news
    except: return []

# --- 2. DME AP Scraping Logic ---
def scrap_dme(driver):
    try:
        driver.get("https://dme.ap.nic.in/")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        links = soup.find_all("a", href=True)
        for l in links:
            title = l.get_text(strip=True)
            if len(title) > 25 and (".pdf" in l['href'].lower() or "202" in title):
                news.append(f"🏛️ *DME AP UPDATE*\n📝 {title}")
        return news[:15]
    except: return []

# --- 3. MCC Scraping Logic (UG, PG, SS) ---
def scrap_mcc(driver):
    urls = {"UG": "https://mcc.nic.in/ug-medical-counselling/", 
            "PG": "https://mcc.nic.in/pg-medical-counselling/",
            "SS": "https://mcc.nic.in/super-speciality-counselling/"}
    news = []
    for cat, url in urls.items():
        try:
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            items = soup.find_all("a", href=True)
            for item in items[:10]:
                text = item.get_text(strip=True)
                if len(text) > 20 and (".pdf" in item['href'].lower() or "notice" in text.lower()):
                    news.append(f"🎓 *MCC {cat} UPDATE*\n📝 {text}")
        except: continue
    return news

# --- 4. NTRUHS Scraping Logic ---
def scrap_ntruhs(driver):
    try:
        driver.get("https://drntr.uhsap.in/index/")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        links = soup.find_all("a", href=True)
        for l in links:
            t = l.get_text(strip=True)
            if len(t) > 30 and ("Admission" in t or "Exam" in t or "202" in t):
                news.append(f"🩺 *NTRUHS UPDATE*\n📝 {t}")
        return news[:15]
    except: return []

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload, verify=False)

def main():
    print("🚀 Anni websites check chestunnanu...")
    driver = get_driver()
    all_current_news = []
    
    all_current_news.extend(scrap_nmc(driver))
    all_current_news.extend(scrap_dme(driver))
    all_current_news.extend(scrap_mcc(driver))
    all_current_news.extend(scrap_ntruhs(driver))
    
    driver.quit()

    # Pattha data check
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()
    else:
        old_news = []

    # New items filter
    new_items = [n for n in all_current_news if n.strip() not in old_news]

    if new_items:
        print(f"✅ {len(new_items)} New updates dhorikaayi!")
        for item in reversed(new_items):
            send_telegram(item)
            time.sleep(1)
        
        # Save current state
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join(all_current_news))
    else:
        print("😴 Kotha updates emi levu.")

if __name__ == "__main__":
    main()
