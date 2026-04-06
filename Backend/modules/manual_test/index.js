import gui_controller
from app_logging import logger  

def run_manual_test():

    try:
        logger.info("Manual test started: Running GUI by gesture")
        gui_controller.run_by_gesture()
        logger.info("Manual test completed successfully")
    except Exception as e:
        logger.exception(f"Exception occurred during manual test: {e}")

#             تنفيذ عند التشغيل مباشر 
if __name__ == "__main__":
    run_manual_test() 
