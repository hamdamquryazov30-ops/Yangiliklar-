import time
import requests
import feedparser
from deep_translator import GoogleTranslator

# ================= SOZLAMALAR =================
BOT_TOKEN = "8911284352:AAG3hsL_5gnpnh6Uah_0JTc3JwbLDcoQxfc"  # BotFather'dan olgan kodingiz
CHANNEL_ID = "@yangiliklar_uzbektilida"     # Kanalingiz usernamesi (masalan: @my_channel)
RSS_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"
CHECK_INTERVAL = 600
# ===============================================

translator = GoogleTranslator(source='en', target='uz')
last_posted_link = ""

def translate_text(text):
    try:
        if not text:
            return ""
        return translator.translate(text)
    except Exception as e:
        print(f"Tarjima xatosi: {e}")
        return text

def send_telegram_message(caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegramga yuborishda xatolik: {e}")

def check_and_post():
    global last_posted_link
    feed = feedparser.parse(RSS_URL)
    
    if feed.entries:
        latest_news = feed.entries[0]
        if latest_news.link != last_posted_link:
            eng_title = latest_news.title
            uzb_title = translate_text(eng_title)
            
            caption = f"🔴 **{uzb_title}**\n\n"
            caption += f"🌐 Batafsil: [Manba maqolasi]({latest_news.link})\n"
            caption += "───\n"
            caption += "🤖 *Avto-tarjima bot*"
            
            send_telegram_message(caption)
            last_posted_link = latest_news.link
            print(f"Yangi post joylandi: {uzb_title}")

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    while True:
        check_and_post()
        time.sleep(CHECK_INTERVAL)
