import sqlite3

DB_NAME = "cartas.db"

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
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
