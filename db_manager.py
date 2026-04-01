import sqlite3
import os

DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        with open('schema.sql', 'r') as f:
            schema = f.read()
        conn = get_db_connection()
        conn.executescript(schema)
        conn.commit()
        conn.close()

def query_db(query, args=(), one=False):
    conn = get_db_connection()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    conn = get_db_connection()
    conn.execute(query, args)
    conn.commit()
    conn.close()
