import requests
from bs4 import BeautifulSoup
import json
import os

URL = "https://www.durhamabc.com/news"
TOPIC = os.environ["NTFY_TOPIC"]
STATE_FILE = ".state.json"

html = requests.get(URL, timeout=20).text
soup = BeautifulSoup(html, "html.parser")

posts = []

for a in soup.find_all("a"):
    title = a.get_text(strip=True)
    href = a.get("href")

    if title and "DROP AVAILABLE NOW" in title.upper():

        if href.startswith("/"):
            href = "https://www.durhamabc.com" + href

        posts.append({
            "title": title,
            "url": href
        })

# load previous state
try:
    with open(STATE_FILE) as f:
        seen = set(json.load(f))
except:
    seen = set()

new_posts = []

for p in posts:
    if p["url"] not in seen:
        new_posts.append(p)

# send notifications
for p in new_posts:

    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=f"{p['title']}\n{p['url']}"
    )

# update state
seen.update([p["url"] for p in posts])

with open(STATE_FILE, "w") as f:
    json.dump(list(seen), f)