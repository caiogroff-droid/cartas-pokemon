from camoufox.sync_api import Camoufox
from bs4 import BeautifulSoup

URL = "https://www.ligapokemon.com.br/?view=cards/card&card=Spiritomb%20(TG09/TG30)&ed=LORTG&num=TG09"

print("🦊 Abrindo Camoufox...")

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    page.goto(URL, wait_until="commit", timeout=30000)
    # Aguarda o elemento da carta aparecer (prova que o Cloudflare liberou)
    page.wait_for_selector(".item-name", timeout=60000)
    html = page.content()

soup = BeautifulSoup(html, "html.parser")

name    = soup.select_one(".item-name")
rarity  = soup.select_one("#details-screen-rarity a")
prices  = soup.select(".container-price-mkp")

print(f"Nome:     {name.get_text(strip=True) if name else '❌ não encontrado'}")
print(f"Raridade: {rarity.get_text(strip=True) if rarity else '❌ não encontrado'}")
print(f"Variantes: {len(prices)} encontradas")
for p in prices:
    code = p.select_one(".extras")
    mn   = p.select_one(".min .price")
    med  = p.select_one(".medium .price")
    mx   = p.select_one(".max .price")
    print(f"  [{code.get_text(strip=True) if code else '?'}] min:{mn.get_text(strip=True) if mn else '?'} med:{med.get_text(strip=True) if med else '?'} max:{mx.get_text(strip=True) if mx else '?'}")