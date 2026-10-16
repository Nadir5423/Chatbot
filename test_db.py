import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    cur = conn.execute("SELECT count(*) FROM threads")
    print("Connected. Threads:", cur.fetchone()[0])