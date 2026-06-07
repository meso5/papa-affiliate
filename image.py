import io
import requests
from PIL import Image, ImageDraw, ImageFont

OUTPUT_PATH = "output.jpg"
SIZE = (1080, 1080)
WATERMARK = "papa_no_honnerevi"


def create_product_image(image_url: str) -> str:
    resp = requests.get(image_url, timeout=15)
    resp.raise_for_status()

    product_img = Image.open(io.BytesIO(resp.content)).convert("RGB")

    canvas = Image.new("RGB", SIZE, "white")

    product_img.thumbnail((900, 900), Image.LANCZOS)
    x = (SIZE[0] - product_img.width) // 2
    y = (SIZE[1] - product_img.height) // 2
    canvas.paste(product_img, (x, y))

    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except Exception:
        font = ImageFont.load_default()

    text = f"@{WATERMARK}"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    margin = 20
    tx = margin
    ty = SIZE[1] - text_h - margin

    draw.rectangle(
        [tx - 8, ty - 4, tx + text_w + 8, ty + text_h + 4],
        fill=(0, 0, 0, 160),
    )
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255))

    canvas.save(OUTPUT_PATH, "JPEG", quality=90)
    return OUTPUT_PATH
