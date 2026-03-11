import os
import json
import requests
from bs4 import BeautifulSoup

URL = "https://www.durhamabc.com/news"
BASE = "https://www.durhamabc.com"
TOPIC = os.environ["NTFY_TOPIC"]
STATE_FILE = ".state.json"

def normalize_url(href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return BASE + href
    return BASE + "/" + href

def send_notification(title: str, url: str):
    requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=f"{title}\n{url}".encode("utf-8"),
        timeout=20,
    )

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def main():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    matches = []
    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        if not title:
            continue

        t = title.upper()
        if "DROP AVAILABLE NOW" in t or "DROP HAPPENING NOW" in t:
            matches.append({
                "title": title,
                "url": normalize_url(a["href"])
            })

    if not matches:
        print("No matching posts found.")
        return

    latest = matches[0]  # assumes newest appears first on page
    state = load_state()
    last_url = state.get("last_url")

    if not last_url:
        # Prime only: save current latest and do NOT notify
        save_state({"last_url": latest["url"]})
        print(f"Primed state with {latest['url']}")
        return

    if latest["url"] != last_url:
        send_notification(latest["title"], latest["url"])
        save_state({"last_url": latest["url"]})
        print(f"New drop detected: {latest['url']}")
    else:
        print("No new matching post.")

if __name__ == "__main__":
    main()
