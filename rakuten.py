import os
import random
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

RAKUTEN_API_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"

# 曜日ごとのジャンルID（月=0, 火=1, ..., 日=6）
GENRE_BY_WEEKDAY = {
    0: ("551177", "抱っこ紐・ベビーカー"),
    1: ("100804", "ベビー服・子供服"),
    2: ("101164", "おもちゃ・知育玩具"),
    3: ("400174", "離乳食・ベビーフード"),
    4: ("400496", "ベビー用品全般"),
    5: ("516503", "PCガジェット・マウス・キーボード"),
    6: ("100533", "カメラ・育児グッズ"),
}

# 除外キーワード（例外商品名に含まれる場合はスキップしない）
EXCLUDE_KEYWORDS = ["水", "ミネラルウォーター", "飲料"]
EXCLUDE_EXCEPTIONS = ["キレートレモン", "北海道コーン茶", "富良野ホップ炭酸水"]


def _is_excluded(item_name: str) -> bool:
    name = item_name
    for exc in EXCLUDE_EXCEPTIONS:
        if exc in name:
            return False
    return any(kw in name for kw in EXCLUDE_KEYWORDS)


def get_random_baby_product(posted_urls=None):
    """商品を取得してランダムに1件返す。
    posted_urls: 投稿済みURLのset。全件投稿済みの場合はリセットして全件から選ぶ。
    戻り値: (product dict, reset_occurred: bool)
    """
    if posted_urls is None:
        posted_urls = set()

    weekday = datetime.now().weekday()
    genre_id, genre_name = GENRE_BY_WEEKDAY[weekday]

    params = {
        "applicationId": os.getenv("RAKUTEN_APP_ID"),
        "affiliateId": os.getenv("RAKUTEN_AFFILIATE_ID"),
        "genreId": genre_id,
        "hits": 30,
        "sort": "-reviewAverage",
        "minReviewCount": 50,
        "formatVersion": 2,
    }

    resp = requests.get(RAKUTEN_API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("Items", [])
    filtered = [
        item for item in items
        if item.get("reviewAverage", 0) >= 4.0
        and item.get("reviewCount", 0) >= 50
        and item.get("mediumImageUrls")
        and not _is_excluded(item.get("itemName", ""))
    ]

    if not filtered:
        raise ValueError(f"条件に合う商品が見つかりませんでした（カテゴリ：{genre_name}）")

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
        "genre_name": genre_name,
    }
    return product, reset_occurred
