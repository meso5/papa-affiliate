import os
import anthropic
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from instagram import post_to_instagram

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

OUTPUT_PATH = "output_intro.jpg"
SIZE = (1080, 1080)
ACCOUNT_NAME = "papa_no_honnerevi"

SYSTEM_PROMPT = """あなたは「ゆうパパ」というInstagramアカウントの中の人です。

【ペルソナ】
名前：ゆうパパ
年齢：33歳
居住：愛知県名古屋市西区
職業：メーカー勤務の会社員
家族：妻・2歳の息子・0歳の息子（子どもの名前は出さない）
趣味：フェス参戦・ラーメン・カメラ・ガジェット・週末のドライブ
性格：細かいことが気になる分析好き。でも文章は気さく。
口癖：「しょうみ」「ほんまに」「あつい」

【口癖の使い方ルール】
- 1投稿につき口癖は1〜2個まで（多用しない）
- 自然な文脈で使う

【絶対に守る禁止事項】
- アスタリスク（**）の使用禁止
- 箇条書きの多用禁止（使うなら全体で1〜2個まで）
- 「まとめると」「結論として」などの硬い接続詞禁止
- 「〜となっています」「〜となっております」などの敬体禁止
- AIっぽい対称構造禁止
- 絵文字の多用禁止（全体で5個以内）
- 名古屋弁は一切使わない

【文体ルール】
- 話し言葉ベースで書く
- ほのかな関西弁口調にする（ガッツリ関西弁ではなく隠し味程度）
- 一文は60文字以内
- 本音っぽいボヤキや笑いを1箇所入れる"""

HASHTAGS = """#はじめまして #自己紹介 #育児パパ #パパの育児 #30代パパ
#二児のパパ #男の子ママ #男の子パパ #パパ育児 #育メン
#育児グッズ #ベビーグッズ #育児用品 #おすすめ育児グッズ #パパ目線レビュー
#本音レビュー #忖度なしレビュー #育児情報 #育児ライフ #新米パパ
#2歳児パパ #0歳児パパ #子育てパパ #子育て情報 #子育てライフ
#パパアカウント #パパインスタ #育児ブログ #子育てブログ #パパの本音"""


def generate_intro_caption() -> str:
    user_prompt = """はじめての自己紹介投稿のキャプションを書いてください。

以下の情報をもとにしてください：
- 名古屋市西区在住の33歳パパ
- 2歳と0歳の息子2人
- メーカー勤務の会社員
- 趣味：フェス参戦・ラーメン・カメラ・ガジェット
- このアカウントを始めた理由：育児グッズ選びで何度も失敗した経験から、パパ目線の本音レビューを発信したい
- 忖度なしで良い点も悪い点も正直に言う

【構成】
1行目：フォロワーへの挨拶（「はじめまして」から始める）
空行
自己紹介本文：家族構成・仕事・趣味をフランクに（4〜6文）
空行
このアカウントの目的：育児グッズ選びで失敗した経験から始めた本音レビューについて（2〜3文）
空行
締め：フォローよろしくの一言

ハッシュタグは含めないでください。システムプロンプトの禁止事項・文体ルールを必ず守って書いてください。"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    body = message.content[0].text
    return f"{body}\n\n{HASHTAGS}"


def create_intro_image() -> str:
    canvas = Image.new("RGB", SIZE, "white")
    draw = ImageDraw.Draw(canvas)

    font_path = "/Library/Fonts/Arial Unicode.ttf"
    try:
        font_large = ImageFont.truetype(font_path, 100)
        font_small = ImageFont.truetype(font_path, 52)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    main_text = "はじめまして👋"
    sub_text = f"@{ACCOUNT_NAME}"

    bbox_main = draw.textbbox((0, 0), main_text, font=font_large)
    main_w = bbox_main[2] - bbox_main[0]
    main_h = bbox_main[3] - bbox_main[1]

    bbox_sub = draw.textbbox((0, 0), sub_text, font=font_small)
    sub_w = bbox_sub[2] - bbox_sub[0]

    gap = 60
    total_h = main_h + gap + (bbox_sub[3] - bbox_sub[1])
    start_y = (SIZE[1] - total_h) // 2

    draw.text(
        ((SIZE[0] - main_w) // 2, start_y),
        main_text,
        font=font_large,
        fill=(30, 30, 30),
    )

    draw.text(
        ((SIZE[0] - sub_w) // 2, start_y + main_h + gap),
        sub_text,
        font=font_small,
        fill=(120, 120, 120),
    )

    canvas.save(OUTPUT_PATH, "JPEG", quality=90)
    print(f"画像を保存しました: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    print("キャプション生成中...")
    caption = generate_intro_caption()
    print("--- 生成されたキャプション ---")
    print(caption)
    print("------------------------------")

    print("画像生成中...")
    image_path = create_intro_image()

    print("Instagram投稿中...")
    post_id = post_to_instagram(image_path, caption)
    print(f"投稿完了: {post_id}")
