import sqlite3
from typing import Optional

DB_PATH = "hangman.db"

# Для простоты используем обычные подключения. Для продакшна можно переключиться на pool/ORM.
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS games (
        chat_id INTEGER PRIMARY KEY,
        word TEXT NOT NULL,
        guessed TEXT NOT NULL,
        wrong INTEGER NOT NULL,
        max_wrong INTEGER NOT NULL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS stats (
        user_id INTEGER PRIMARY KEY,
        wins INTEGER NOT NULL DEFAULT 0,
        losses INTEGER NOT NULL DEFAULT 0
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        chat_id INTEGER PRIMARY KEY,
        lang TEXT NOT NULL DEFAULT 'en'
    )
    """)
    conn.commit()
    conn.close()

# --- games ---
def save_game(chat_id: int, word: str, guessed: str, wrong: int, max_wrong: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO games (chat_id, word, guessed, wrong, max_wrong) VALUES (?, ?, ?, ?, ?)",
        (chat_id, word, guessed, wrong, max_wrong),
    )
    conn.commit()
    conn.close()

def load_game(chat_id: int) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT word, guessed, wrong, max_wrong FROM games WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    word, guessed, wrong, max_wrong = row
    return { 'word': word, 'guessed': set(guessed), 'wrong': wrong, 'max_wrong': max_wrong }

def delete_game(chat_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM games WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# --- stats ---
def inc_win(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO stats (user_id, wins, losses) VALUES (?, 1, 0) ON CONFLICT(user_id) DO UPDATE SET wins = wins + 1", (user_id,))
    conn.commit()
    conn.close()

def inc_loss(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO stats (user_id, wins, losses) VALUES (?, 0, 1) ON CONFLICT(user_id) DO UPDATE SET losses = losses + 1", (user_id,))
    conn.commit()
    conn.close()

def get_stats(user_id: int) -> tuple:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT wins, losses FROM stats WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return (0, 0)
    return row[0], row[1]

# --- settings ---
def set_lang(chat_id: int, lang: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (chat_id, lang) VALUES (?, ?)", (chat_id, lang))
    conn.commit()
    conn.close()

def get_lang(chat_id: int) -> str:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT lang FROM settings WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return 'en'
    return row[0]
