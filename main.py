import subprocess
import time

from playwright.sync_api import sync_playwright

from database import init_database, get_conn
from scraper import get_card_html, parse_card, print_card
from csv_export import export_csv

def add_card(browser, link, state):
    html = get_card_html(browser, link)
    card = parse_card(html)

    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO cartas
        (link, name, rarity, current_state)
        VALUES (?, ?, ?, ?)
        """, (link, card.name, card.rarity, state))

        cursor.execute(
            "DELETE FROM carta_variantes WHERE link_carta = ?",
            (link,)
        )

        for variant in card.variants:
            cursor.execute("""
            INSERT INTO carta_variantes
            (
                link_carta,
                code,
                variant_name,
                min,
                medium,
                max
            )
            VALUES (?, ?, ?, ?, ?, ?)
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

        cursor.execute(
            "SELECT link, current_state FROM cartas"
        )

        for link, state in cursor.fetchall():
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
    init_database()

    chrome = subprocess.Popen(
        [
            "google-chrome",
            "--remote-debugging-port=9222",
            "--user-data-dir=/tmp/chrome-debug",
            "--disable-logging",
            "--log-level=3",
            "--silent",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(3)

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
