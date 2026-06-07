from bs4 import BeautifulSoup
from models import Cards, Variant, CardState
from parser_novo import QUALITY, EXTRAS, parse_card_new

def get_card_html(browser, link: str) -> str:
    context = browser.contexts[0]
    page = context.new_page()

    try:
        page.goto(
    link,
    wait_until="load",
    timeout=60000
)

        try:
            page.wait_for_selector(
    ".item-name",
    timeout=120000
)
        except Exception:
            pass
        
        return page.content()

    finally:
        page.close()

def parse_card(html: str, link: str) -> Cards:
    soup = BeautifulSoup(html, "html.parser")

    name_tag = soup.select_one(".item-name")
    rarity_tag = soup.select_one("#details-screen-rarity a")

    variants = []

    prices = parse_card_new(html).prices
    if (prices == None):
        prices = {}


    for bloco in soup.select(".container-price-mkp"):
        name = (
    bloco.select_one(".container-extras span").get_text(strip=True)
    if bloco.select_one(".container-extras span")
    else ""
)
        variants.append(
            Variant(
                code=bloco.select_one(".extras").get_text(strip=True)
                if bloco.select_one(".extras") else "",
                name=name,
                min=bloco.select_one(".min .price").get_text(strip=True)
                if bloco.select_one(".min .price") else "",
                medium=bloco.select_one(".medium .price").get_text(strip=True)
                if bloco.select_one(".medium .price") else "",
                max=bloco.select_one(".max .price").get_text(strip=True)
                if bloco.select_one(".max .price") else "",
                favorite=False,
                prices_per_state={
                    k: v
                    for k, v in prices.items()
                    if name in k
                }
            )
        )
    

    return Cards(
        name=name_tag.get_text(strip=True) if name_tag else "",
        link=link,
        rarity=rarity_tag.get_text(strip=True) if rarity_tag else "",
        variants=variants,

    )

def print_card(card: Cards):
    print("\n" + "=" * 60)
    print(f"Nome: {card.name}")
    print(f"Raridade: {card.rarity}")

    for variant in card.variants:
        print(f"\n[{variant.code}] {variant.name}")
        print(
            f"Min: {variant.min} | "
            f"Médio: {variant.medium} | "
            f"Max: {variant.max}"
        )

    print("=" * 60)
