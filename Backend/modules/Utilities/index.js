from app_logging import logger  

def validate_name(name):

   #          التحقق من أن الاسم صالح (مش فاضي)
    if not name or name.strip() == "":
        logger.warning("Validation failed: name is empty or invalid")
        return False
    logger.info(f"Validation passed for name: {name}")
    return True

def format_text(text):
    
   # تنسيق النص: إزالة الفراغات وتحويل الحروف الأولى لكابيتال
    formatted = text.strip().title()
    logger.info(f"Formatted text: '{text}' → '{formatted}'")
    return formatted
