import sqlite3
from app_logging import logger  

def connect_db():
    try:
        conn = sqlite3.connect("neurix.db")
        logger.info("Connected to database 'neurix.db'")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def create_tables():
    conn = connect_db()
    if conn is None:
        logger.error("Cannot create tables because database connection failed")
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS designs (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        conn.commit()
        logger.info("Tables created successfully (designs)")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
    finally:
        conn.close()
        logger.info("Database connection closed after creating tables")

if __name__ == "__main__":
    create_tables()
