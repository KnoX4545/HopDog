import os
import psycopg2
import json
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        data JSONB NOT NULL
    )
    """)

    conn.commit()
    cur.close()
    conn.close()


def save_user(user_id, data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users (user_id, data)
    VALUES (%s, %s)
    ON CONFLICT (user_id)
    DO UPDATE SET data = EXCLUDED.data
    """, (
        user_id,
        json.dumps(data)
    ))

    conn.commit()
    cur.close()
    conn.close()


def load_user(user_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT data FROM users WHERE user_id=%s",
        (user_id,)
    )

    result = cur.fetchone()

    cur.close()
    conn.close()

    if result:
        return result["data"]

    return None


def all_users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    cur.close()
    conn.close()

    return users
