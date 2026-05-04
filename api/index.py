import os
import requests
from flask import Flask, request
import telebot

# ========== কনফিগারেশন ==========
BOT_TOKEN = "8725024459:AAEcL5waEF9eWGjZ1vCXt1Uo56VnENLag00"
API_KEY = "r3f6PifXWq7w6XLjXJVHFKgMCngyieVW8sySBB38O7"
EXTRACT_PICS_URL = "https://api.extract.pics/v0/extractions"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# ========== বট হ্যান্ডলার ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "👋 Magnific বট!\n\n"
        "ব্যবহার:\n"
        "/photo [URL] - ছবি পাওয়ার জন্য URL দিন\n"
        "/get [ID] - ১ মিনিট পর আইডি দিয়ে ছবি আনুন"
    )

@bot.message_handler(commands=['photo'])
def handle_photo(message):
    url = message.text.replace("/photo", "").strip()
    
    if not url:
        bot.reply_to(message, "❌ লিঙ্ক দিন।\n\nউদাহরণ: /photo https://www.magnific.com/premium-photo/xxxxx.htm")
        return
    
    bot.reply_to(message, "🚀 এক্সট্রাকশন শুরু হচ্ছে...")
    
    try:
        res = requests.post(
            EXTRACT_PICS_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={"url": url},
            timeout=30
        )
        
        if res.status_code in [200, 201]:
            data = res.json()
            ext_id = data["data"]["id"]
            
            bot.send_message(
                message.chat.id,
                f"✅ এক্সট্রাকশন শুরু হয়েছে!\n\n🆔 আইডি: {ext_id}\n\n"
                f"⏳ 1 মিনিট পরে এই কমান্ড দিন:\n/get {ext_id}"
            )
        else:
            bot.reply_to(message, f"❌ API ত্রুটি: {res.status_code}")
            
    except Exception as e:
        bot.reply_to(message, f"❌ ত্রুটি: {str(e)}")

@bot.message_handler(commands=['get'])
def get_result(message):
    ext_id = message.text.replace("/get", "").strip()
    
    if not ext_id:
        bot.reply_to(message, "❌ আইডি দিন।\n\nউদাহরণ: /get d22ead09-3ae0-4866-bb72-d3d0a0db7b9c")
        return
    
    bot.reply_to(message, "🔍 ছবি খোঁজা হচ্ছে...")
    
    try:
        res = requests.get(
            f"{EXTRACT_PICS_URL}/{ext_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        
        if res.status_code == 200:
            data = res.json()
            status = data["data"]["status"]
            
            if status == "done":
                images = data["data"].get("images", [])
                
                # ছবির URL ফিল্টার
                photo_urls = []
                for img in images:
                    img_url = img.get("url", "")
                    if "img.magnific.com/premium-photo/" in img_url and "?w=" not in img_url:
                        if img_url not in photo_urls:
                            photo_urls.append(img_url)
                
                if photo_urls:
                    bot.send_message(message.chat.id, f"✅ {len(photo_urls)} টি ছবি পাওয়া গেছে!")
                    
                    # URL লিস্ট দেখানো
                    url_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(photo_urls[:10])])
                    bot.send_message(message.chat.id, f"📸 ছবির লিংক:\n{url_list}")
                    
                    # ছবি পাঠানো
                    for i, url in enumerate(photo_urls[:5]):
                        try:
                            bot.send_photo(message.chat.id, url, caption=f"ছবি {i+1}/{len(photo_urls)}")
                        except:
                            bot.send_message(message.chat.id, f"ছবি {i+1}: {url}")
                else:
                    bot.reply_to(message, "❌ কোনো ছবির লিংক পাওয়া যায়নি।")
                    
            elif status == "pending":
                bot.reply_to(message, "⏳ এখনও pending অবস্থায় আছে। আরও 1 মিনিট পর চেষ্টা করুন।")
            else:
                bot.reply_to(message, f"❌ এক্সট্রাকশন ব্যর্থ হয়েছে। স্ট্যাটাস: {status}")
        else:
            bot.reply_to(message, "❌ আইডিটি সঠিক নয় বা মেয়াদ শেষ।")
            
    except Exception as e:
        bot.reply_to(message, f"❌ ত্রুটি: {str(e)}")

# ========== ওয়েবহুক ==========
@app.route('/api/index', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Method Not Allowed', 405

@app.route('/')
def index():
    return "Magnific Photo Bot is running on Vercel!"

# ========== লোকাল রানের জন্য ==========
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
