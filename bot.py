import os
import time
import re
import threading
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from flask import Flask

# ---------------------------------------------------------
# 1. SOZLAMALAR
# ---------------------------------------------------------
BOT_TOKEN = "8911284352:AAG3hsL_5gnpnh6Uah_0JTc3JwbLDcoQxfc"
CHANNEL_ID = "@yangiliklar_uzbektilida"

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

CHECK_INTERVAL = 600  # Har 10 daqiqada tekshirish
SEEN_POSTS_FILE = "seen_posts.txt"

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 24/7 faol ishlamoqda!", 200

# ---------------------------------------------------------
# 2. YORDAMCHI FUNKSIYALAR
# ---------------------------------------------------------
def load_seen_posts():
    if os.path.exists(SEEN_POSTS_FILE):
        with open(SEEN_POSTS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_seen_post(post_id):
    with open(SEEN_POSTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{post_id}\n")

def translate_text(text):
    if not text:
        return ""
    try:
        translated = GoogleTranslator(source='auto', target='uz').translate(text[:4000])
        return translated
    except Exception as e:
        print(f"Tarjima xatosi: {e}")
        return text

def scrape_full_article(url):
    """Sayt havolasiga kirib, to'liq maqolani ajratib oladi"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        paragraphs = soup.find_all('p')
        full_text = []
        for p in paragraphs:
            txt = p.get_text().strip()
            if len(txt) > 40 and not any(word in txt.lower() for word in ['copyright', 'privacy policy', 'subscribe', 'terms']):
                full_text.append(txt)
            if len(full_text) >= 6: # Post optimal hajmda bo'lishi uchun 6 ta asosiy paragraf
                break
                
        return "\n\n".join(full_text)
    except Exception as e:
        print(f"Scraping xatosi ({url}): {e}")
        return ""

def send_telegram_message(title, full_text):
    uz_title = translate_text(title)
    uz_text = translate_text(full_text)
    
    message = f"📰 **{uz_title}**\n\n{uz_text}"
    if len(message) > 4000:
        message = message[:3990] + "...\n\n*(Batafsil matn qisqartirildi)*"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print(f"To'liq post kanalga joylandi: {title}")
        else:
            print(f"Telegramga yuborishda xatolik: {res.text}")
    except Exception as e:
        print(f"Xatolik: {e}")

# ---------------------------------------------------------
# 3. ASOSIY SIKL
# ---------------------------------------------------------
def check_and_post():
    seen_posts = load_seen_posts()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                post_id = entry.get("id", entry.link)
                
                if post_id not in seen_posts:
                    title = entry.title
                    link = entry.link
                    
                    article_text = scrape_full_article(link)
                    
                    if not article_text:
                        article_text = entry.get("summary", "")
                        
                    send_telegram_message(title, article_text)
                    
                    seen_posts.add(post_id)
                    save_seen_post(post_id)
                    time.sleep(5)
        except Exception as e:
            print(f"RSS xatosi ({feed_url}): {e}")

def start_bot_loop():
    print("Bot ishga tushdi...")
    while True:
        try:
            check_and_post()
        except Exception as e:
            print(f"Siklda xatolik: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=start_bot_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
