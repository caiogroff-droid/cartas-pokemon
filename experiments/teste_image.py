import os
import re
import json
import requests

from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO


def extract_sprite_url(html):
    m = re.search(
        r'background-image:url\((.*?)\)',
        html,
        re.DOTALL
    )

    if not m:
        raise RuntimeError("Sprite não encontrada")

    url = m.group(1).strip('"').strip("'")

    if url.startswith("//"):
        url = "https:" + url

    return url


def extract_css_positions(html):
    positions = {}

    pattern = re.compile(
        r'\.([A-Za-z0-9]+)\s*\{[^}]*background-position:([-\d]+)px\s+([-\d]+)px',
        re.DOTALL
    )

    for cls, x, y in pattern.findall(html):
        positions[cls] = (
            abs(int(x)),
            abs(int(y))
        )

    return positions


def extract_cards_stock(html):
    m = re.search(
        r'var cards_stock\s*=\s*(\[.*?\]);',
        html,
        re.DOTALL
    )

    if not m:
        raise RuntimeError("cards_stock não encontrado")

    return json.loads(m.group(1))


def download_sprite(url):
    print("Baixando sprite...")
    r = requests.get(url)
    r.raise_for_status()

    return Image.open(BytesIO(r.content))


def dump_preco_css_images(
    stock,
    positions,
    sprite,
    width=14,
    height=21,
):
    os.makedirs("digits", exist_ok=True)

    count = 0

    for item in stock:

        preco_css = item.get("precoCss")

        if not preco_css:
            continue

        print("\n=== NOVO PREÇO ===")
        print(preco_css)

        tokens = preco_css.split(";")

        for i, token in enumerate(tokens):

            classes = token.split()

            digit_class = None

            for cls in classes:
                if cls in positions:
                    digit_class = cls
                    break

            if not digit_class:
                print("Classe não encontrada:", token)
                continue

            x, y = positions[digit_class]

            crop = sprite.crop(
                (
                    x,
                    y,
                    x + width,
                    y + height
                )
            )

            filename = (
                f"digits/"
                f"{count}_{i}_{digit_class}.png"
            )

            crop.save(filename)

            print(
                f"{digit_class}"
                f" -> {filename}"
            )

        count += 1

        if count >= 5:
            break


def main():

    with open("debug.html", encoding="utf8") as f:
        html = f.read()

    sprite_url = extract_sprite_url(html)

    print("Sprite:")
    print(sprite_url)

    positions = extract_css_positions(html)

    print(
        f"Classes encontradas: "
        f"{len(positions)}"
    )

    stock = extract_cards_stock(html)

    print(
        f"Registros stock: "
        f"{len(stock)}"
    )

    sprite = download_sprite(sprite_url)

    dump_preco_css_images(
        stock,
        positions,
        sprite
    )


if __name__ == "__main__":
    main()