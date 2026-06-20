import sqlite3
from models import Variant
from variables import *

DB_NAME = "cartas.db"

def get_conn():
    conn = sqlite3.connect(
        "cartas.db",
        timeout=30,
        check_same_thread=False
    )

    conn.execute("PRAGMA journal_mode=WAL")

    return conn

def init_database():
    with get_conn() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cartas (
            link TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            rarity TEXT,
            current_state TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS carta_variantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_carta TEXT NOT NULL,
            code TEXT,
            variant_name TEXT,
            min TEXT,
            medium TEXT,
            max TEXT,
            favorite BOOLEAN,
            UNIQUE(link_carta, variant_name),
            FOREIGN KEY (link_carta)
                REFERENCES cartas(link)
                ON DELETE CASCADE
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS carta_precos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    link_carta TEXT NOT NULL,
    variant_name TEXT NOT NULL,
    card_state TEXT NOT NULL,

    min_price TEXT,
    favorite BOOLEAN,

    UNIQUE(link_carta, variant_name, card_state),

    FOREIGN KEY (link_carta)
        REFERENCES cartas(link)
        ON DELETE CASCADE
)
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_name
        ON cartas(name)
        """)

        conn.commit()

def toggleOwned(link: str, variant_name: str):
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

def getDatabaseData(conn):
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
    return cards,variants,prices

def addDatatoDatabase(conn, card, link):
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO cartas
        (link, name, rarity, current_state)
        VALUES (?, ?, ?, ?)
        """, (link, card.name, card.rarity, ""))


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

