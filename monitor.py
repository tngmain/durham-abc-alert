import os
import json
import requests
from bs4 import BeautifulSoup

URL = "https://www.durhamabc.com/news"
BASE = "https://www.durhamabc.com"
TOPIC = os.environ["NTFY_TOPIC"]
STATE_FILE = ".state.json"

MATCH_PHRASES = [
    "DROP AVAILABLE NOW",
    "DROP HAPPENING NOW",
    "DROP: AVAILABLE NOW",
]

def normalize_url(href: str) -> str:
    href = href.strip()
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return BASE + href
    return BASE + "/" + href

def is_match(title: str) -> bool:
    t = " ".join(title.upper().split())
    return any(p in t for p in MATCH_PHRASES)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_notification(title: str, url: str):
    r = requests.post(
        f"https://ntfy.sh/{TOPIC}",
        data=f"{title}\n{url}".encode("utf-8"),
        timeout=20,
    )
    r.raise_for_status()

def main():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    matches = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        href = a["href"].strip()

        if not title or not is_match(title):
            continue

        url = normalize_url(href)
        if url in seen_urls:
            continue
        seen_urls.add(url)

        matches.append({"title": title, "url": url})

    print(f"Found {len(matches)} matching post(s).")
    for m in matches[:5]:
        print(f"- {m['title']} -> {m['url']}")

    if not matches:
        print("No matching posts found.")
        return

    latest = matches[0]
    state = load_state()
    last_url = state.get("last_url")

    print(f"Latest detected URL: {latest['url']}")
    print(f"Last saved URL: {last_url}")

    if not last_url:
        save_state({"last_url": latest["url"]})
        print("Primed state; no notification sent.")
        return

    if latest["url"] != last_url:
        send_notification(latest["title"], latest["url"])
        save_state({"last_url": latest["url"]})
        print("New drop detected; notification sent.")
    else:
        print("No new matching post.")

if __name__ == "__main__":
    main()
