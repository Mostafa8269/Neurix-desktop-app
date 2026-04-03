import logging

logger = logging.getLogger("NeurixApp")
logger.setLevel(logging.DEBUG)  # يسجل كل شيء DEBUG وما فوق

# التأكد إن مفيش Handlers مكررة
if not logger.handlers:
    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # ممكن تغيري لـ DEBUG لو تحبي

    # File Handler
    fh = logging.FileHandler("neurix.log")
    fh.setLevel(logging.DEBUG)

    # Format موحد
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # إضافة الـ Handlers للـ Logger
    logger.addHandler(ch)
    logger.addHandler(fh)

#                         دوال مساعدة 
def log_info(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)

def log_error(message):
    logger.error(message)

def log_exception(message):
    logger.exception(message)
