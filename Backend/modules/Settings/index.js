from database import connect_db
from app_logging import logger  

def change_theme(theme):

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # إنشاء جدول لو مش موجود
        cursor.execute("CREATE TABLE IF NOT EXISTS settings (theme TEXT)")

        # مسح القديم
        cursor.execute("DELETE FROM settings")

        # إضافة الجديد
        cursor.execute("INSERT INTO settings (theme) VALUES (?)", (theme,))

        conn.commit()
        logger.info(f"Theme updated to: {theme}")

    except Exception as e:
        logger.error(f"Failed to change theme to '{theme}': {e}")

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed after changing theme")

def get_settings():
    
    try:
        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("SELECT theme FROM settings")
        data = cursor.fetchone()

        logger.info(f"Fetched settings: {data}")
        return data

    except Exception as e:
        logger.error(f"Failed to fetch settings: {e}")
        return None

    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed after fetching settings")
