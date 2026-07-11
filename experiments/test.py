import requests
from bs4 import BeautifulSoup

URL = "https://www.ligapokemon.com.br/?view=cards/card&card=Spiritomb%20C%20(003/016)&ed=PTHD&num=003"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    )
}

response = requests.get(URL, headers=headers, timeout=30)

print("=" * 50)
print("STATUS:", response.status_code)
print("URL FINAL:", response.url)
print("=" * 50)

html = response.text

# Salva para inspeção manual
with open("debug_requests.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Tamanho HTML:", len(html))

# Procura alguns indicadores
checks = [
    "Spiritomb",
    "container-price-mkp",
    "item-name",
    "security verification",
    "captcha",
    "cloudflare",
]

print("\nIndicadores encontrados:")
for check in checks:
    print(f"{check}: {check.lower() in html.lower()}")

print("\nPrimeiros 1000 caracteres:")
print(html[:1000])

# Teste rápido de parse
soup = BeautifulSoup(html, "html.parser")

name = soup.select_one(".item-name")

print("\nNome encontrado:")
print(name.get_text(strip=True) if name else "NÃO ENCONTRADO")