from database import connect_db
from app_logging import logger  

def create_user(username):

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # إنشاء جدول المستخدمين لو مش موجود
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)

        # إضافة مستخدم
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()

        logger.info(f"User created: {username}")

    except Exception as e:
        logger.error(f"Failed to create user '{username}': {e}")

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed after creating user")

def get_users():
    
   # جلب كل المستخدمين من قاعدة البيانات
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
        logger.info(f"Fetched {len(data)} users from database")
        return data

    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        return []

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed after fetching users")
