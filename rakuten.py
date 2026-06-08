import os
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

RAKUTEN_API_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"

# 曜日ごとの検索キーワード（月=0, 火=1, ..., 日=6）
KEYWORD_BY_WEEKDAY = {
    0: "抱っこ紐",
    1: "ベビー服 男の子",
    2: "知育おもちゃ",
    3: "離乳食 グッズ",
    4: "ベビー用品 便利",
    5: "キーボード ワイヤレス",
    6: "ミラーレス カメラ",
}

FALLBACK_KEYWORD = "育児グッズ"

EXCLUDE_KEYWORDS = ["水", "ミネラルウォーター", "飲料"]
EXCLUDE_EXCEPTIONS = ["キレートレモン", "北海道コーン茶", "富良野ホップ炭酸水"]


def _is_excluded(item_name: str) -> bool:
    name = item_name
    for exc in EXCLUDE_EXCEPTIONS:
        if exc in name:
            return False
    return any(kw in name for kw in EXCLUDE_KEYWORDS)


def _fetch_items(params: dict) -> list:
    resp = requests.get(RAKUTEN_API_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("Items", [])


def _filter_items(items: list, min_review_avg=3.0, min_review_count=5) -> list:
    return [
        item for item in items
        if item.get("reviewAverage", 0) >= min_review_avg
        and item.get("reviewCount", 0) >= min_review_count
        and item.get("mediumImageUrls")
        and not _is_excluded(item.get("itemName", ""))
    ]


def get_random_baby_product(posted_urls=None):
    """商品を取得してランダムに1件返す。必ず1件以上返す。
    posted_urls: 投稿済みURLのset。全件投稿済みの場合はリセットして全件から選ぶ。
    戻り値: (product dict, reset_occurred: bool)
    """
    if posted_urls is None:
        posted_urls = set()

    weekday = datetime.now().weekday()
    keyword = KEYWORD_BY_WEEKDAY[weekday]

    base_params = {
        "applicationId": os.getenv("RAKUTEN_APP_ID"),
        "affiliateId": os.getenv("RAKUTEN_AFFILIATE_ID"),
        "hits": 30,
        "sort": "-reviewAverage",
        "formatVersion": 2,
    }

    # キーワード検索（評価3.0以上・レビュー5件以上）
    items = _fetch_items({**base_params, "keyword": keyword})
    filtered = _filter_items(items, min_review_avg=3.0, min_review_count=5)

    # 条件なしで再検索
    if not filtered and items:
        filtered = [
            item for item in items
            if item.get("mediumImageUrls")
            and not _is_excluded(item.get("itemName", ""))
        ]

    # フォールバック：「育児グッズ」で検索
    if not filtered:
        items = _fetch_items({**base_params, "keyword": FALLBACK_KEYWORD})
        filtered = _filter_items(items, min_review_avg=3.0, min_review_count=5)

    # 最終フォールバック：条件なし
    if not filtered and items:
        filtered = [
            item for item in items
            if item.get("mediumImageUrls")
        ]

    if not filtered:
        raise ValueError("商品が1件も取得できませんでした")

    unposted = [
        item for item in filtered
        if (item.get("affiliateUrl") or item["itemUrl"]) not in posted_urls
    ]

    reset_occurred = False
    if not unposted:
        unposted = filtered
        reset_occurred = True

    item = random.choice(unposted)

    product = {
        "name": item["itemName"],
        "price": item["itemPrice"],
        "review_average": item["reviewAverage"],
        "review_count": item["reviewCount"],
        "item_url": item["itemUrl"],
        "affiliate_url": item.get("affiliateUrl") or item["itemUrl"],
        "image_url": (
            item["mediumImageUrls"][0]["imageUrl"]
            if isinstance(item["mediumImageUrls"][0], dict)
            else item["mediumImageUrls"][0]
        ).replace("128x128", "500x500"),
        "shop_name": item["shopName"],
        "catch_copy": item.get("catchcopy", ""),
        "genre_name": keyword,
    }
    return product, reset_occurred
