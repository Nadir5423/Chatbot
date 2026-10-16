from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import DATABASE_URL

# Neon closes idle connections, so check each one before handing it out.
pool = ConnectionPool(
    DATABASE_URL,
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row},
    check=ConnectionPool.check_connection,
    open=False,
)