import json
import os

POSTED_FILE = os.path.join(os.path.dirname(__file__), "posted_products.json")


def load_posted_urls():
    if not os.path.exists(POSTED_FILE):
        return set()
    with open(POSTED_FILE) as f:
        return set(json.load(f))


def save_posted_url(url):
    urls = load_posted_urls()
    urls.add(url)
    with open(POSTED_FILE, "w") as f:
        json.dump(list(urls), f, ensure_ascii=False, indent=2)


def reset_posted_urls():
    with open(POSTED_FILE, "w") as f:
        json.dump([], f)
