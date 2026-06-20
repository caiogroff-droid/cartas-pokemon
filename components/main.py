from enum import Enum
import subprocess
import time
import platform
import os

from playwright.sync_api import sync_playwright

from database import init_database, get_conn
from scraper import get_card_html, parse_card, print_card
from csv_export import export_csv
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
from models import Cards, Variant

app = FastAPI()
app.mount("/static", StaticFiles(directory="../static"), name="static")

templates = Jinja2Templates(
    directory="../templates"
)


cartas: dict[str, Cards] = {}
loading: bool = False

class FilterType(Enum):
    OWNED = 1
    NOT_OWNED = 2
    HAS_PRICE_DATA = 3
    ALL = 0
    
currentfilterType = FilterType.ALL
lastSearch: str = ''

@app.get("/reset")
def reset(request: Request):
    global currentfilterType
    currentfilterType = FilterType.ALL
    return home(request)

@app.post("/change-filter")
def change_filter(request: Request, owned: str | None = Form(None)):
    print(owned)
    global currentfilterType
    match owned:
        case 'on':
            currentfilterType = FilterType.OWNED
        case None:
            currentfilterType = FilterType.ALL
    return search(request, lastSearch)
    
def load_cards():
    with get_conn() as conn:

        
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                link,
                name,
                rarity,
                current_state
            FROM cartas
        """)
        cards = cursor.fetchall()

        cursor.execute("""
            SELECT
                link_carta,
                code,
                variant_name,
                min,
                medium,
                max,
                favorite, 
                id
            FROM carta_variantes
        """)
        variants = cursor.fetchall()

        cursor.execute("""
            SELECT
                link_carta,
                card_state,
                variant_name,
                min_price,
                favorite
            FROM carta_precos        
        """)
        prices = cursor.fetchall()



        cartas.clear()
        cartas.update({
            card[0]: Cards(
                link=card[0],
                name=card[1],
                rarity=card[2],
                variants=[
                    Variant(
                        code=variant[1],
                        name=variant[2],
                        min=variant[3],
                        medium=variant[4],
                        max=variant[5],
                        favorite=bool(variant[6]),
                        prices_per_state={
                            price[1]: price[3]
                            for price in prices
                            if price[0] == card[0] and price[2] == variant[2]
                        }
                    )
                    for variant in variants
                    if variant[0] == card[0] and checkFilterType(variant, currentfilterType)
                ]
            )
            for card in cards
            
        })
    

init_database()
@app.get("/")
def home(request: Request):
    

    load_cards()


    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "cartas": cartas,
            "tableScreen": True
        }
    )

def checkFilterType(variant, filter: FilterType):
    match filter:
        case FilterType.ALL:
            return True
        case FilterType.OWNED:
            if variant[6] and bool(variant[6]):
                print(variant[2] + 'returned True')
                return True
            else:
                print(variant[2] + 'returned False')
                return False
            
        case FilterType.NOT_OWNED:
            if variant[6] and bool(variant[6]):
                return True
    return False

@app.get("/search")
def search(
    request: Request,
    search: str = "",
):
    load_cards()
    cartas_filtradas = {
        link: card
        for link, card in cartas.items()
        if search.lower() in card.name.lower()
    }
    cartas.clear()
    cartas.update(cartas_filtradas)
    global lastSearch
    lastSearch = search
    return templates.TemplateResponse(
        request=request,
        name="partials/card_table.html",
        context={
            "cartas": cartas
        }
    )

@app.post("/toggle_favorite")
def toggle_favorite(
    request: Request,
    link: str = Form(...),
    variant_name: str = Form(...),
):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE carta_variantes
            SET favorite = CASE WHEN favorite THEN 0 ELSE 1 END
            WHERE link_carta = ? AND variant_name = ?
        """, (link, variant_name))
        conn.commit()

        cartas[link].variants = [
            Variant(
                code=variant.code,
                name=variant.name,
                min=variant.min,
                medium=variant.medium,
                max=variant.max,
                favorite=not variant.favorite if variant.name == variant_name else variant.favorite,
                prices_per_state=variant.prices_per_state
            )
            for variant in cartas[link].variants
        ]

    return templates.TemplateResponse(
        request=request,
        name="partials/variant_row.html",
        context={
            "variant": next(variant for variant in cartas[link].variants if variant.name == variant_name),
            "link": link,
            "card": cartas[link]
        }
    )

@app.get("/add-card")
def add_card_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="add_card_form.html",
        context={
            "loading": loading,
            "tableScreen": False
        }
    )

@app.post("/add-card")
def add_card_confirm(
    request: Request,
    links: str = Form(...)
):
    lista_links = [
        l.strip()
        for l in links.splitlines()
        if l.strip()
    ]
    loading = True

    if platform.system() == "Windows":
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        debug_path = "--user-data-dir=C:\\temp\\chrome-debug"



        if not os.path.exists(chrome_exe):
            chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    else:
        chrome_exe = "google-chrome"
        debug_path = "--user-data-dir=chrome-debug"

    chrome = subprocess.Popen(
    [
        chrome_exe,
        "--remote-debugging-port=9222",
        debug_path,
        "--disable-logging",
        "--log-level=3",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

    time.sleep(3)

    global browser

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(
                "http://127.0.0.1:9222"
            )

            for l in lista_links:
                try:
                    if ("http" not in l):
                        base_link = "https://www.ligapokemon.com.br/?view=cards/card&card="
                        partes = l.rsplit(" ", 1)
                        resultado = f"{partes[0]} ({partes[1]})"
                        add_card(browser, base_link + resultado, "")
                    else:
                        add_card(browser, l, "")
                except Exception as e:
                    print(f"Erro ao adicionar carta {l}: {e}")
            

    except Exception as e:
        print(f"Erro ao conectar ao Chrome: {e}")
        loading = False
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "cartas": cartas,
            }
        )
    
    finally:
        chrome.terminate()
        loading = False
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "cartas": cartas,
                "tableScreen": True
            }
        )



    

def add_card(browser, link, state):
    html = get_card_html(browser, link)
    card = parse_card(html, link)

    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO cartas
        (link, name, rarity, current_state)
        VALUES (?, ?, ?, ?)
        """, (link, card.name, card.rarity, state))


        for variant in card.variants:
            for state, price in variant.prices_per_state.items():
                cursor.execute("""
INSERT INTO carta_precos
(
    link_carta,
    variant_name,
    card_state,
    min_price,
    favorite
)
VALUES (?, ?, ?, ?, 0)

ON CONFLICT(link_carta, variant_name, card_state)
DO UPDATE SET
    min_price = excluded.min_price
""", (
    link,
    variant.name,
    state,
    price,
))
            cursor.execute("""
INSERT INTO carta_variantes
(
    link_carta,
    code,
    variant_name,
    min,
    medium,
    max,
    favorite
)
VALUES (?, ?, ?, ?, ?, ?, 0)

ON CONFLICT(link_carta, variant_name)
DO UPDATE SET
    code = excluded.code,
    min = excluded.min,
    medium = excluded.medium,
    max = excluded.max
""", (
    link,
    variant.code,
    variant.name,
    variant.min,
    variant.medium,
    variant.max,
))
        conn.commit()


    print_card(card)

def update_cards(browser):
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT link, current_state
            FROM cartas
        """)

        cards = cursor.fetchall()

    # conexão fechou aqui

    for link, state in cards:
        add_card(browser, link, state)

def list_cards():
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT name, rarity, current_state
        FROM cartas
        """)

        for card in cursor.fetchall():
            print(
                f"Nome: {card[0]} | "
                f"Raridade: {card[1]} | "
                f"Estado: {card[2]}"
            )

def export_cards():
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            c.name,
            c.rarity,
            v.code,
            v.variant_name,
            v.min,
            v.medium,
            v.max,
            c.current_state
            v.favorite
        FROM cartas c
        LEFT JOIN carta_variantes v
        ON c.link = v.link_carta
        """)

        export_csv(cursor.fetchall())

def menu():
    return """
0 - Sair
1 - Adicionar carta
2 - Listar cartas
3 - Exportar CSV
4 - Atualizar cartas
"""

def main():

    if platform.system() == "Windows":
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        if not os.path.exists(chrome_exe):
            chrome_exe = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    else:
        chrome_exe = "google-chrome"

    chrome = subprocess.Popen(
    [
        chrome_exe,
        "--remote-debugging-port=9222",
        "--user-data-dir=chrome-debug",
        "--disable-logging",
        "--log-level=3",
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
    time.sleep(3)

    global browser

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(
                "http://127.0.0.1:9222"
            )

            while True:

                option = input(menu()).strip()

                if option == "0":
                    break

                elif option == "1":
                    link = input("Link: ")
                    state = input(
                        "Estado (condição ou descrição, essa informação é irrelevante pra busca. Enter para ignorar): "
                    )
                    add_card(browser, link, state)

                elif option == "2":
                    list_cards()

                elif option == "3":
                    export_cards()
                    print("cartas.csv gerado")

                elif option == "4":
                    update_cards(browser)

    finally:
        chrome.terminate()

if __name__ == "__main__":
    main()
