# import os
# import time
# import requests
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager

# BOT_TOKEN = os.getenv("BOT_TOKEN")
# CHAT_ID = os.getenv("CHAT_ID")
# FILE_NAME = "old.txt"

# def get_driver():
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--window-size=1920,1080")
#     # Bypass SSL & Cert errors
#     chrome_options.add_argument("--ignore-certificate-errors")
#     chrome_options.add_argument("--allow-insecure-localhost")
    
#     service = Service(ChromeDriverManager().install())
#     return webdriver.Chrome(service=service, options=chrome_options)

# def scrap_site(driver, url, site_name):
#     print(f"🔍 Checking {site_name}...")
#     try:
#         driver.get(url)
#         time.sleep(5) # Wait for JS to load
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         news = []
        
#         links = soup.find_all("a", href=True)
#         for l in links:
#             t = l.get_text(strip=True)
#             # Basic filter for meaningful links
#             if len(t) > 20:
#                 news.append(f"📌 *{site_name} UPDATE*\n📝 {t}")
        
#         return news[:10] # Top 10 matrame
#     except Exception as e:
#         print(f"❌ Error in {site_name}: {e}")
#         return []

# def main():
#     if not BOT_TOKEN or not CHAT_ID:
#         print("❌ Secrets missing!")
#         return

#     driver = get_driver()
#     all_news = []
    
#     # List of websites to check
#     sites = [
#         ("https://www.nmc.org.in/all-news/", "NMC"),
#         ("https://dme.ap.nic.in/", "DME AP"),
#         ("https://mcc.nic.in/ug-medical-counselling/", "MCC UG"),
#         ("https://drntr.uhsap.in/index/", "NTRUHS")
#     ]
    
#     for url, name in sites:
#         all_news.extend(scrap_site(driver, url, name))
    
#     driver.quit()

#     if os.path.exists(FILE_NAME):
#         with open(FILE_NAME, "r", encoding="utf-8") as f:
#             old_news = f.read().splitlines()
#     else:
#         old_news = []

#     new_items = [n for n in all_news if n.strip() not in old_news]

#     if new_items:
#         print(f"🚀 Found {len(new_items)} new updates!")
#         telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
#         for item in reversed(new_items):
#             requests.post(telegram_url, data={"chat_id": CHAT_ID, "text": item, "parse_mode": "Markdown"}, verify=False)
#             time.sleep(1)
        
#         with open(FILE_NAME, "w", encoding="utf-8") as f:
#             f.write("\n".join(all_news))
#     else:
#         print("😴 No updates.")

# if __name__ == "__main__":
#     main()

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

# Basic Config
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FILE_NAME = "old.txt"

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.page_load_strategy = 'eager'
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrap_nmc(driver):
    try:
        driver.get("https://www.nmc.org.in/all-news/")
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        rows = soup.find("table").find_all("tr")
        for row in rows[1:15]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                # NMC Format: News ID -> Description -> Published on
                n_id = cols[0].get_text(strip=True)
                date = cols[1].get_text(strip=True)
                desc = cols[2].get_text(strip=True)
                
                msg = (f"NMC News Alert:\n📌 *NMC UPDATE*\n"
                       f"News ID : {n_id}\n\n"
                       f"Description\n📝 {desc}\n\n"
                       f"Published on\n{date}")
                news.append(msg)
        return news
    except: return []

def scrap_others(driver, url, name):
    try:
        driver.get(url)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        news = []
        
        # NTRUHS and MCC common link finder
        links = soup.find_all("a", href=True)
        for l in links:
            subject = l.get_text(strip=True)
            # General filters for subject
            if len(subject) > 30 and any(keyword in subject for keyword in ["202", "Notice", "Admission", "Counseling", "Notification"]):
                
                # Migitha websites ki: Kevalam Subject (Description) & Published on (Date)
                # Note: Vere sites lo date dorakkapothe "Latest" ani chupisthundi
                msg = (f"{name} News Alert:\n📌 *{name} UPDATE*\n\n"
                       f"Subject\n📝 {subject}\n\n"
                       f"Published on\nLatest Update")
                news.append(msg)
        return news[:8]
    except: return []

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Secrets missing!")
        return
        
    driver = get_driver()
    all_current = []
    
    # NMC separately with ID format
    all_current.extend(scrap_nmc(driver))
    
    # Others with Subject/Date format
    all_current.extend(scrap_others(driver, "https://mcc.nic.in/ug-medical-counselling/", "MCC UG"))
    all_current.extend(scrap_others(driver, "https://drntr.uhsap.in/index/", "NTRUHS"))
    all_current.extend(scrap_others(driver, "https://dme.ap.nic.in/", "DME AP"))
    
    driver.quit()

    # Comparison Logic
    old_news = []
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            old_news = f.read().splitlines()

    new_items = [n for n in all_current if n.replace('\n', ' ').strip() not in [o.replace('\n', ' ').strip() for o in old_news]]

    if new_items:
        t_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        for item in reversed(new_items):
            requests.post(t_url, data={"chat_id": CHAT_ID, "text": item, "parse_mode": "Markdown"}, verify=False)
            time.sleep(1)
        
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            f.write("\n".join([n.replace('\n', ' ') for n in all_current]))
    else:
        print("😴 No new updates.")

if __name__ == "__main__":
    main()
