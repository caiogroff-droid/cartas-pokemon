import subprocess
import time
import platform
import os

from playwright.sync_api import sync_playwright

from database import addDatatoDatabase, get_conn, getDatabaseData
from models import Variant
from variables import *
from csv_export import export_csv
from scraper import get_card_html, parse_card, print_card


def load_cards():
    with get_conn() as conn:
        
        cards, variants, prices = getDatabaseData(conn)
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


def addCardstoDatabase(lista_links: list[str]):
    if platform.system() == "Windows":
        chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        debug_path = f"--user-data-dir={os.environ.get('LOCALAPPDATA')}\\Google\\Chrome\\User Data"


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
                        add_card(browser, base_link + resultado)
                    else:
                        add_card(browser, l)
                except Exception as e:
                    print(f"Erro ao adicionar carta {l}: {e}")
            

    except Exception as e:
        print(f"Erro ao conectar ao Chrome: {e}")
        return
    
    finally:
        chrome.terminate()
        return
    

def add_card(browser, link):
    html = get_card_html(browser, link)
    card = parse_card(html, link)

    with get_conn() as conn:
        addDatatoDatabase(conn, card, link)

    print_card(card)

def reset_filter():
    global currentfilterType
    currentfilterType = FilterType.ALL

def filter_to(owned):
    global currentfilterType
    match owned:
        case 'on':
            currentfilterType = FilterType.OWNED
        case None:
            currentfilterType = FilterType.ALL