import time
import requests
import feedparser
from deep_translator import GoogleTranslator

# ================= SOZLAMALAR =================
BOT_TOKEN = "8911284352:AAG3hsL_5gnpnh6Ua..."  # O'zingizning to'liq tokeningizni tekshirib oling
CHANNEL_ID = "@yangiliklar_uzbektilida"

# Bir nechta ishonchli yangiliklar manbalari:
RSS_URLS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",      # BBC World
    "https://www.aljazeera.com/xml/rss/all.xml",       # Al Jazeera
    "http://rss.cnn.com/rss/edition.rss"               # CNN
]

CHECK_INTERVAL = 600  # Har 10 daqiqada tekshiradi
# ===============================================

translator = GoogleTranslator(source='en', target='uz')
posted_links = set()

def translate_text(text):
    """Matnni o'zbek tiliga tarjima qilish"""
    try:
        if not text:
            return ""
        # Juda uzun matnlarni bo'lib tarjima qilish uchun
        if len(text) > 4500:
            text = text[:4500]
        return translator.translate(text)
    except Exception as e:
        print(f"Tarjimada xatolik: {e}")
        return text

def send_telegram_message(text):
    """Telegram kanalga post joylash"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload)
        return res.status_code == 200
    except Exception as e:
        print(f"Telegramga yuborishda xatolik: {e}")
        return False

def check_and_post():
    """Manbalarni tekshirish va batafsil post tayyorlash"""
    print("Yangi xabarlar tekshirilmoqda...")
    for rss_url in RSS_URLS:
        try:
            feed = feedparser.parse(rss_url)
            if not feed.entries:
                continue
                
            latest = feed.entries[0]
            link = latest.link
            
            if link not in posted_links:
                title_en = latest.title
                summary_en = getattr(latest, 'summary', title_en)
                
                # O'zbek tiliga tarjima qilish
                title_uz = translate_text(title_en)
                summary_uz = translate_text(summary_en)
                
                # Chiroyli va batafsil post formati
                post_text = f"📌 <b>{title_uz}</b>\n\n"
                post_text += f"📝 {summary_uz}\n\n"
                post_text += "🌐 <b>Dunyoda nima gap?</b> — <i>Eng so'nggi va muhim xabarlar kanalamizda!</i>"
                
                if send_telegram_message(post_text):
                    posted_links.add(link)
                    print(f"Yangi post joylandi: {title_uz}")
                    time.sleep(5)
        except Exception as e:
            print(f"RSS o'qishda xatolik ({rss_url}): {e}")

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    while True:
        check_and_post()
        time.sleep(CHECK_INTERVAL)

import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Render "Timed Out" xatosini bermasligi uchun bepul port tinglovchi
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot 24/7 ishlamoqda!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Fonda mini serverni ishga tushirish
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("Bot ishga tushdi...")
    while True:
        check_and_post()
        time.sleep(CHECK_INTERVAL)

