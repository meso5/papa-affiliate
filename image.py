import io
import requests
from PIL import Image, ImageDraw, ImageFont

OUTPUT_PATH = "output.jpg"
SIZE = (1080, 1080)
WATERMARK = "@papa_no_honnerevi"
BG_COLOR = (245, 245, 245)
BANNER_HEIGHT = 100
BANNER_ALPHA = 160
PRODUCT_IMG_MAX = 1000


def _load_font(size: int) -> ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _fit_image(img: Image.Image, max_size: int) -> Image.Image:
    ratio = min(max_size / img.width, max_size / img.height)
    new_w = max(1, int(img.width * ratio))
    new_h = max(1, int(img.height * ratio))
    return img.resize((new_w, new_h), Image.LANCZOS)


def create_product_image(image_url: str, product_name: str = "") -> str:
    resp = requests.get(image_url, timeout=15)
    resp.raise_for_status()

    product_img = Image.open(io.BytesIO(resp.content)).convert("RGB")

    canvas = Image.new("RGB", SIZE, BG_COLOR)

    product_img = _fit_image(product_img, PRODUCT_IMG_MAX)
    x = (SIZE[0] - product_img.width) // 2
    y = (SIZE[1] - product_img.height) // 2
    canvas.paste(product_img, (x, y))

    # 半透明バナー（商品名用）
    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle(
        [0, SIZE[1] - BANNER_HEIGHT, SIZE[0], SIZE[1]],
        fill=(0, 0, 0, BANNER_ALPHA),
    )
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # 商品名をバナー中央に表示
    if product_name:
        name_font = _load_font(28)
        truncated = product_name if len(product_name) <= 20 else product_name[:20] + "…"
        bbox = draw.textbbox((0, 0), truncated, font=name_font)
        name_w = bbox[2] - bbox[0]
        name_h = bbox[3] - bbox[1]
        name_x = (SIZE[0] - name_w) // 2
        name_y = SIZE[1] - BANNER_HEIGHT + (BANNER_HEIGHT - name_h) // 2
        draw.text((name_x, name_y), truncated, font=name_font, fill=(255, 255, 255))

    # ウォーターマーク：右下（18px、白）
    wm_font = _load_font(18)
    wm_bbox = draw.textbbox((0, 0), WATERMARK, font=wm_font)
    wm_w = wm_bbox[2] - wm_bbox[0]
    wm_h = wm_bbox[3] - wm_bbox[1]
    margin = 16
    wm_x = SIZE[0] - wm_w - margin
    wm_y = SIZE[1] - wm_h - margin
    draw.text((wm_x, wm_y), WATERMARK, font=wm_font, fill=(255, 255, 255))

    canvas.save(OUTPUT_PATH, "JPEG", quality=90)
    return OUTPUT_PATH
