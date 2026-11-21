
import requests, json, os, sys, time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

URL = "https://egy.voxcinemas.com/movies/whatson"
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

# الاتصال بموقع VOX مع إعادة المحاولة
html = None

for attempt in range(3):
    try:
        print(f"جاري الاتصال بموقع VOX... محاولة {attempt + 1}")

        response = requests.get(
            URL,
            timeout=(15, 60),
            headers={"User-Agent": "Mozilla/5.0"}
        )

        response.raise_for_status()
        html = response.text
        break

    except requests.exceptions.RequestException as e:
        print("فشل الاتصال:", e)
        time.sleep(5)

if html is None:
    sys.exit("تعذر الاتصال بموقع VOX بعد 3 محاولات")

soup = BeautifulSoup(html, "html.parser")

movies = {}

for a in soup.select('a[href^="/movies/"]'):
    href = a.get("href", "")

    if href.rstrip("/") in ("/movies/whatson", "/movies/comingsoon"):
        continue

    name = a.get("title") or a.get_text(strip=True)

    if name:
        movies[href] = name

print("لقيت", len(movies), "فيلم")

if not movies:
    sys.exit("مفيش أفلام اتقرأت")

seen = set(json.load(open(FILE))) if os.path.exists(FILE) else set()

for href in movies.keys() - seen:
    try:
        result = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": f"🎬 فيلم جديد نزل: {movies[href]}\n{urljoin(URL, href)}"
            },
            timeout=20
        )

        result.raise_for_status()

        if result.json().get("ok"):
            print("تم إرسال:", movies[href])
            seen.add(href)

    except requests.exceptions.RequestException as e:
        print("فشل إرسال الإشعار:", e)

json.dump(sorted(seen), open(FILE, "w"))
