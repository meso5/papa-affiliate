import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

RAKUTEN_API_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"


def get_random_baby_product(posted_urls=None):
    """商品を取得してランダムに1件返す。
    posted_urls: 投稿済みURLのset。全件投稿済みの場合はリセットして全件から選ぶ。
    戻り値: (product dict, reset_occurred: bool)
    """
    if posted_urls is None:
        posted_urls = set()

    params = {
        "applicationId": os.getenv("RAKUTEN_APP_ID"),
        "affiliateId": os.getenv("RAKUTEN_AFFILIATE_ID"),
        "genreId": "559887",
        "hits": 30,
        "sort": "-reviewAverage",
        "minReviewCount": 100,
        "formatVersion": 2,
    }

    resp = requests.get(RAKUTEN_API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("Items", [])
    filtered = [
        item for item in items
        if item.get("reviewAverage", 0) >= 4.0
        and item.get("reviewCount", 0) >= 100
        and item.get("mediumImageUrls")
    ]

    if not filtered:
        raise ValueError("条件に合う商品が見つかりませんでした")

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
        "affiliate_url": item.get("affiliateUrl") or item["itemUrl"],
        "image_url": (
            item["mediumImageUrls"][0]["imageUrl"]
            if isinstance(item["mediumImageUrls"][0], dict)
            else item["mediumImageUrls"][0]
        ).replace("128x128", "500x500"),
        "shop_name": item["shopName"],
        "catch_copy": item.get("catchcopy", ""),
    }
    return product, reset_occurred
