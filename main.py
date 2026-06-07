import logging
import sys
from datetime import datetime
from rakuten import get_random_baby_product
from caption import generate_caption
from image import create_product_image
from instagram import post_to_instagram
from posted_products import load_posted_urls, save_posted_url, reset_posted_urls


def _write_room_log(product: dict) -> None:
    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = (
        "=====\n"
        f"日付：{date_str}\n"
        f"商品名：{product['name']}\n"
        f"楽天アフィリエイトURL：{product['affiliate_url']}\n"
        f"画像URL：{product['image_url']}\n"
        "=====\n"
    )
    with open("room_log.txt", "a", encoding="utf-8") as f:
        f.write(entry)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def main():
    try:
        log.info("=== papa-affiliate 自動投稿開始 ===")

        posted_urls = load_posted_urls()
        log.info(f"投稿済み商品数: {len(posted_urls)}件")

        log.info("楽天商品取得中...")
        product, reset_occurred = get_random_baby_product(posted_urls)
        if reset_occurred:
            log.info("全件投稿済みのためposted_products.jsonをリセットします")
            reset_posted_urls()
        log.info(f"商品: {product['name']} ({product['price']}円)")

        log.info("キャプション生成中...")
        caption = generate_caption(product)
        log.info(f"キャプション生成完了（{len(caption)}文字）")

        log.info("画像加工中...")
        image_path = create_product_image(product["image_url"])
        log.info(f"画像保存: {image_path}")

        log.info("Instagram投稿中...")
        post_id = post_to_instagram(image_path, caption)
        log.info(f"投稿成功: post_id={post_id}")

        save_posted_url(product["affiliate_url"])
        log.info(f"投稿済みURLを記録: {product['affiliate_url']}")

        _write_room_log(product)
        log.info("room_log.txtに記録しました")

        log.info("=== 完了 ===")

    except Exception as e:
        log.error(f"エラーが発生しました: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
