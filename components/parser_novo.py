import json
import re
from bs4 import BeautifulSoup
from models import CardState

# Mapeamentos
QUALITY = {1:"M (Nova)", 2:"NM (Praticamente Nova)", 3:"SP (Usada Levemente)",
           4:"MP (Usada Moderadamente)", 5:"HP (Muito Usada)", 6:"D (Danificada)"}
EXTRAS  = {0:"Normal", 2:"Foil", 3:"Reverse Foil", 5:"Edition One", 7:"Promo",
           11:"Assinada", 13:"Pre Release", 17:"Alterada", 19:"Staff",
           23:"Textless", 29:"Oversize", 31:"Shadowless", 37:"Misprint",
           41:"Shattered Holo", 43:"Master Ball", 47:"Pokeball Foil"}


def parse_card_new(html: str) -> CardState:
    soup = BeautifulSoup(html, "html.parser")

    # ── Nome e raridade ──────────────────────────────────────────────────────
    name_tag   = soup.select_one(".item-name")
    rarity_tag = soup.select_one("#details-screen-rarity a")
    name   = name_tag.get_text(strip=True)   if name_tag   else ""
    rarity = rarity_tag.get_text(strip=True) if rarity_tag else ""

    # ── Extrai cards_stock do JavaScript ────────────────────────────────────
    script_text = ""
    for tag in soup.find_all("script"):
        if tag.string and "cards_stock" in tag.string:
            script_text = tag.string
            break

    stock_raw = re.search(r"var cards_stock\s*=\s*(\[.*?\]);", script_text, re.DOTALL)
    if not stock_raw:
        return CardState(
                name=name,
                rarity=rarity,
                prices={}
            )
        

    stock = json.loads(stock_raw.group(1))

    # ── Menor preço por (qualidade, extras) ─────────────────────────────────
    best = {}  # chave: (qualid, extras) → menor precoFinal

    for item in stock:
        if item.get("sellType", 1) != 1:  # ignora leilões (sellType=2)
            continue

        preco_str = item.get("precoFinal") or item.get("preco")
        if not preco_str:
            continue

        try:
            preco = float(preco_str)
        except ValueError:
            print(f"⚠️ Preço inválido: {preco_str}")
            continue

        qualid = item.get("qualid", 0)
        extras = item.get("extras", 0)
        chave  = (qualid, extras)
        print(f"📌 Encontrado: qualid={qualid} extras={extras} preco={preco:.2f}")
        if chave not in best or preco < best[chave]:
            best[chave] = preco

    # ── Organiza resultado ───────────────────────────────────────────────────
    prices = {}
    for (qualid, extras), preco in sorted(best.items()):
        qual_label  = QUALITY.get(int(qualid))
        extra_label = EXTRAS.get(extras, f"Extra {extras}")
        key = f"{qual_label} | {extra_label}"
        prices[key] = f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return CardState(
        name=name,
        rarity=rarity,
        prices=prices
    )

def print_card(card: CardState):
    print(f"\nNome:     {card.name}")
    print(f"Raridade: {card.rarity}")
    print(f"\n{'Qualidade':<45} {'Menor Preço':>12}")
    print("-" * 58)
    if card.prices:
        for label, preco in card.prices.items():
            print(f"{label:<45} {preco:>12}")


if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "debug.html"
    with open(filepath, encoding="utf-8") as f:
        html = f.read()
    card = parse_card_new(html)
    print_card(card)