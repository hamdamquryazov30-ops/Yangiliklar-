import os
import requests
import feedparser
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------------------------------------------------
# 1. SOZLAMALAR
# ---------------------------------------------------------
BOT_TOKEN = "8911284352:AAG3hsL_5gnpnh6Uah_0JTc3JwbLDcoQxfc"
CHANNEL_ID = "@yangiliklar_uzbektilida"

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
]

SEEN_POSTS_FILE = "seen_posts.txt"

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
            if len(full_text) >= 4:
                break
                
        return "\n\n📌 ".join(full_text)
    except Exception as e:
        print(f"Scraping xatosi: {e}")
        return ""

def fetch_one_new_article():
    seen_posts = load_seen_posts()
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            post_id = entry.get("id", entry.link)
            if post_id not in seen_posts:
                title = entry.title
                link = entry.link
                full_text = scrape_full_article(link)
                if not full_text:
                    full_text = entry.get("summary", "")
                
                save_seen_post(post_id)
                return title, full_text
    return None, None

# ---------------------------------------------------------
# 3. BOT KOMANDALARI
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Menyuda katta va aniq tugma chiqarish
    keyboard = [['🚀 Post joylash']]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "Assalomu alaykum!\nKanalga chiroyli post joylash uchun pastdagi **'🚀 Post joylash'** tugmasini bosing yoki botiingizga shunchaki `/post` deb yozing.",
        reply_markup=markup
    )

async def post_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Yangilik tayyorlanmoqda...")
    
    title, full_text = fetch_one_new_article()
    
    if not title:
        await update.message.reply_text("❌ Hozircha yangi o'qilmagan yangilik topilmadi.")
        return

    uz_title = translate_text(title)
    uz_text = translate_text(full_text)

    # Premium Chiroyli Dizayn
    message = (
        f"🌐 **DUNYO HABARLARI** | **RASMIY MANBA**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔥 **{uz_title.upper()}**\n\n"
        f"📌 {uz_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ *Dunyodagi eng muhim voqealar va yangiliklar faqat bizning kanalda!*\n\n"
        f"📲 **A'zo bo'ling:** 👉 [Yangiliklar Uzbekistan](https://t.me/yangiliklar_uzbektilida)"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    res = requests.post(url, json=payload)
    if res.status_code == 200:
        await update.message.reply_text("✨ Chiroyli post muvaffaqiyatli kanalga joylandi!")
    else:
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {res.text}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Buyruqlar va matnli xabarlarni ushlash
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, post_command))
    
    print("Bot ishlamoqda...")
    app.run_polling()
