import base64
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("META_LONG_TOKEN")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
BASE_URL = f"https://graph.facebook.com/v19.0/{ACCOUNT_ID}"


def _post_with_retry(method, url, max_retries=3, **kwargs):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.request(method, url, **kwargs)
            if not resp.ok:
                print(f"[DEBUG] {method} {url} -> {resp.status_code}")
                print(f"[DEBUG] レスポンス本文: {resp.text}")
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            print(f"リトライ {attempt}/{max_retries}（{wait}秒後）: {e}")
            time.sleep(wait)


def upload_to_imgbb(image_path: str) -> str:
    print(f"[DEBUG] imgbbアップロード開始: {image_path}")
    print(f"[DEBUG] IMGBB_API_KEY 設定済み: {bool(IMGBB_API_KEY)}")
    with open(image_path, "rb") as f:
        raw = f.read()
    encoded = base64.b64encode(raw).decode("utf-8")
    print(f"[DEBUG] base64エンコード完了: {len(encoded)}文字")
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": IMGBB_API_KEY, "image": encoded},
    )
    print(f"[DEBUG] imgbb ステータス: {resp.status_code}")
    print(f"[DEBUG] imgbb レスポンス: {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()
    url = data["data"]["url"]
    print(f"[DEBUG] imgbb URL: {url}")
    assert url.startswith("https://"), f"image_urlがhttpsではありません: {url}"
    return url


def post_to_instagram(image_path: str, caption: str) -> str:
    print(f"[DEBUG] INSTAGRAM_ACCOUNT_ID 設定済み: {bool(ACCOUNT_ID)}")
    print(f"[DEBUG] META_LONG_TOKEN 設定済み: {bool(ACCESS_TOKEN)}")
    print(f"[DEBUG] トークン先頭10文字: {ACCESS_TOKEN[:10] if ACCESS_TOKEN else 'None'}")

    image_url = upload_to_imgbb(image_path)
    print(f"[DEBUG] image_url https確認: {image_url.startswith('https://')}")

    # Step1: コンテナ作成
    container = _post_with_retry(
        "POST",
        f"{BASE_URL}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        },
    )
    container_id = container["id"]
    print(f"コンテナ作成完了: {container_id}")

    time.sleep(5)

    # Step2: 投稿公開
    publish = _post_with_retry(
        "POST",
        f"{BASE_URL}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": ACCESS_TOKEN,
        },
    )
    post_id = publish["id"]
    print(f"投稿完了: {post_id}")
    return post_id
