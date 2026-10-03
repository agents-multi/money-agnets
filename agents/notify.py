"""Optional Telegram alerts. Does nothing if the secrets are not set."""
import os, json, urllib.request


def alert(msg):
    print("[ALERT]", msg)
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data=json.dumps({"chat_id": chat, "text": msg}).encode(),
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)
    except Exception as e:
        print("Telegram failed:", e)
