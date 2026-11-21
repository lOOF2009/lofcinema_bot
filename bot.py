
import requests
import json
import os
import sys

TOKEN = os.environ["TOKEN"]

API = f"https://api.telegram.org/bot{TOKEN}"

SUBSCRIBERS_FILE = "subscribers.json"
OFFSET_FILE = "offset.json"


def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)


def send_message(chat_id, text):
    try:
        requests.post(
            f"{API}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": text
            },
            timeout=15
        ).raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Send error: {e}")


subscribers = set(
    str(x) for x in load_json(SUBSCRIBERS_FILE, [])
)

offset = load_json(OFFSET_FILE, 0)

try:
    response = requests.get(
        f"{API}/getUpdates",
        params={
            "offset": offset,
            "timeout": 0,
            "allowed_updates": json.dumps(["message"])
        },
        timeout=20
    )

    response.raise_for_status()
    updates = response.json()

    if not updates.get("ok"):
        sys.exit("Telegram API error")

    for update in updates["result"]:
        offset = update["update_id"] + 1

        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))

        if not chat_id or chat.get("type") != "private":
            continue

        command = message.get("text", "").split()[0].split("@")[0] if message.get("text") else ""

        if command == "/start":
            if chat_id not in subscribers:
                subscribers.add(chat_id)
                send_message(
                    chat_id,
                    "أهلاً بيك في Scene Cinemas Bot! 🎬\n\n"
                    "تم تسجيل اشتراكك بنجاح.\n"
                    "هنبعتلك إشعار لما يبدأ حجز فيلم جديد.\n\n"
                    "لإلغاء الاشتراك استخدم /stop"
                )
                print("New subscriber:", chat_id)
            else:
                send_message(chat_id, "أنت مشترك بالفعل! 🎬")

        elif command == "/stop":
            if chat_id in subscribers:
                subscribers.remove(chat_id)
                send_message(chat_id, "تم إلغاء اشتراكك بنجاح.")
                print("Unsubscribed:", chat_id)
            else:
                send_message(chat_id, "أنت مش مشترك حاليًا.")

        elif command == "/help":
            send_message(
                chat_id,
                "🎬 Scene Cinemas Bot\n\n"
                "/start - الاشتراك\n"
                "/stop - إلغاء الاشتراك\n"
                "/help - المساعدة"
            )

    save_json(SUBSCRIBERS_FILE, sorted(subscribers))
    save_json(OFFSET_FILE, offset)

    print("Subscribers:", len(subscribers))
    print("Updates processed:", len(updates["result"]))

except requests.exceptions.RequestException as e:
    sys.exit(f"Telegram connection error: {e}")
