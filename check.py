
import requests
import json
import os
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup

URL = "https://cfc.scenecinemas.com/home"
TOKEN = os.environ["TOKEN"]

SEEN_FILE = "seen.json"
SUBSCRIBERS_FILE = "subscribers.json"

headers = {"User-Agent": "Mozilla/5.0"}
API = f"https://api.telegram.org/bot{TOKEN}"


def load_json(file, default):
    if not os.path.exists(file):
        return default

    try:
        with open(file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# تحميل المشتركين والأفلام السابقة
subscribers = load_json(SUBSCRIBERS_FILE, [])
seen = set(load_json(SEEN_FILE, []))

print("عدد المشتركين:", len(subscribers))

# الاتصال بموقع Scene Cinemas
try:
    response = requests.get(
        URL,
        timeout=(15, 45),
        headers=headers
    )
    response.raise_for_status()
    html = response.text

except requests.exceptions.RequestException as e:
    sys.exit(f"فشل الاتصال بموقع Scene: {e}")

soup = BeautifulSoup(html, "html.parser")

movies = {}

for a in soup.select('a[href*="/movie-details"]'):
    href = a.get("href", "")
    name = a.get("title") or a.get_text(strip=True)

    if href and name:
        movies[href] = name

print("لقيت", len(movies), "فيلم")

if not movies:
    sys.exit("لم يتم العثور على أفلام. لم يتم تعديل seen.json")

# إرسال الأفلام الجديدة للمشتركين
new_movies = set(movies) - seen

for href in sorted(new_movies):
    movie_name = movies[href]
    movie_url = urljoin(URL, href)

    message = (
        f"🎬 فيلم جديد على Scene Cinemas!\n\n"
        f"🎥 {movie_name}\n\n"
        f"🔗 {movie_url}"
    )

    all_sent = True

    for chat_id in subscribers:
        try:
            result = requests.post(
                f"{API}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": message
                },
                timeout=20
            )

            result.raise_for_status()

            if not result.json().get("ok"):
                all_sent = False
                print("فشل إرسال الإشعار إلى:", chat_id)

        except requests.exceptions.RequestException as e:
            all_sent = False
            print("خطأ في الإرسال:", e)

    if all_sent:
        seen.add(href)
        print("تم إرسال:", movie_name)
    else:
        print("سيتم إعادة محاولة إرسال:", movie_name)

save_json(SEEN_FILE, sorted(seen))

print("انتهى الفحص.")
