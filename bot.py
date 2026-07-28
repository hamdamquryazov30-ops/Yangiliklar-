import os
import time
import threading
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from flask import Flask

# ---------------------------------------------------------
# 1. SOZLAMALAR (TOKEN VA SOZLAMALAR)
# ---------------------------------------------------------
BOT_TOKEN = "8911284352:AAG3hsL_5gnpnh6Uah_0JTc3JwbLDcoQxfc"
CHANNEL_ID = "@yangiliklar_uzbektilida"  # Masalan: @yangiliklar_kanali

# RSS Yangiliklar manbalari
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

CHECK_INTERVAL = 600  # Har 10 daqiqada tekshirish (sekundda)
SEEN_POSTS_FILE = "seen_posts.txt"

# ---------------------------------------------------------
# 2. RENDER UCHUN MINI-SERVER (PORT TINGLOVCHI)
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 24/7 faol ishlamoqda!", 200

# ---------------------------------------------------------
# 3. YORDAMCHI FUNKSIYALAR
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
    try:
        translated = GoogleTranslator(source='auto', target='uz').translate(text)
        return translated
    except Exception as e:
        print(f"Tarjima qilishda xatolik: {e}")
        return text

def send_telegram_message(title, link):
    uz_title = translate_text(title)
    message = f"📢 **{uz_title}**\n\n🔗 [Batafsil o'qish]({link})"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print(f"Post kanalga joylandi: {title}")
        else:
            print(f"Telegramga yuborishda xatolik: {res.text}")
    except Exception as e:
        print(f"So'rov yuborishda xatolik: {e}")

# ---------------------------------------------------------
# 4. ASOSIY TEKSHIRUV SIKLI
# ---------------------------------------------------------
def check_and_post():
    seen_posts = load_seen_posts()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]: # Oxirgi 5 ta xabarni tekshirish
                post_id = entry.get("id", entry.link)
                
                if post_id not in seen_posts:
                    title = entry.title
                    link = entry.link
                    
                    send_telegram_message(title, link)
                    
                    seen_posts.add(post_id)
                    save_seen_post(post_id)
                    time.sleep(3) # Ketma-ket spam bo'lmasligi uchun
        except Exception as e:
            print(f"RSS o'qishda xatolik ({feed_url}): {e}")

def start_bot_loop():
    print("Bot ishga tushdi va xabarlarni kutmoqda...")
    while True:
        try:
            check_and_post()
        except Exception as e:
            print(f"Siklda xatolik: {e}")
        time.sleep(CHECK_INTERVAL)

# ---------------------------------------------------------
# 5. ISHGA TUSHIRISH
# ---------------------------------------------------------
if __name__ == "__main__":
    # Botni alohida fonda (thread) ishga tushirish
    threading.Thread(target=start_bot_loop, daemon=True).start()
    
    # Render portal ajratgan PORT ni tinglash
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
