
import requests
import json
import os
import sys
from urllib.parse import urljoin
from bs4 import BeautifulSoup

URL = "https://cfc.scenecinemas.com/home"
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
FILE = "seen.json"

headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(URL, timeout=30, headers=headers)
    response.raise_for_status()
    html = response.text
except requests.exceptions.RequestException as e:
    sys.exit(f"فشل الاتصال بموقع Scene: {e}")

soup = BeautifulSoup(html, "html.parser")

movies = {}

for a in soup.select('a[href*="/movie-details"]'):
    name = a.get("title") or a.get_text(strip=True)

    if name:
        movies[a["href"]] = name

print("لقيت", len(movies), "فيلم")

if not movies:
    sys.exit("مفيش أفلام اتقرأت")

seen = set(json.load(open(FILE))) if os.path.exists(FILE) else set()

for href in movies.keys() - seen:
    result = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": f"🎬 فيلم جديد على Scene Cinemas: {movies[href]}\n{urljoin(URL, href)}"
        },
        timeout=20
    )

    result.raise_for_status()

    if result.json().get("ok"):
        print("تم إرسال:", movies[href])
        seen.add(href)

with open(FILE, "w") as f:
    json.dump(sorted(seen), f)
