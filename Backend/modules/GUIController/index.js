import logic_view, logic_new, logic_settings, logic_more
from gesture_integration import detect_gesture
from app_logging import logger  

def button_clicked(button_name):
    """
    التعامل مع الضغط على الأزرار في الواجهة
    """
    logger.info(f"Button clicked: {button_name}")

    if button_name == "View":
        logic_view.run_logic()
        logger.info("Executed logic_view.run_logic()")

    elif button_name == "New":
        logic_new.run_logic()
        logger.info("Executed logic_new.run_logic()")

    elif button_name == "Settings":
        logic_settings.run_logic()
        logger.info("Executed logic_settings.run_logic()")

    elif button_name == "More":
        logic_more.run_logic()
        logger.info("Executed logic_more.run_logic()")

    else:
        logger.warning(f"Unknown button clicked: {button_name}")

def run_by_gesture():
    
    gesture = detect_gesture()
    logger.info(f"Gesture received: {gesture}")

    if gesture == "hand_up":
        logic_new.run_logic()
        logger.info("Executed logic_new.run_logic() via gesture 'hand_up'")

    elif gesture == "swipe_left":
        logic_view.run_logic()
        logger.info("Executed logic_view.run_logic() via gesture 'swipe_left'")

    elif gesture == "swipe_right":
        logic_settings.run_logic()
        logger.info("Executed logic_settings.run_logic() via gesture 'swipe_right'")

    elif gesture == "open_hand":
        logic_more.run_logic()
        logger.info("Executed logic_more.run_logic() via gesture 'open_hand'")

    elif gesture == "fist":
        logger.info("Gesture 'fist' detected → Exiting App")
        exit()

    else:
        logger.warning(f"Gesture not recognized: {gesture}")
