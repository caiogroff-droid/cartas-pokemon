import sqlite3

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
