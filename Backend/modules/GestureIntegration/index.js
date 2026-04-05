from app_logging import logger  

known_gestures = ["hand right", "hand up", "hand down"]  

def detect_gesture():

# مؤقت: قراءة gesture من الكيبورد لمحاكاة الكاميرا.
    gesture = input("Enter gesture: ").strip()
    logger.info(f"Simulated gesture detected: {gesture}")
    return gesture


def handle_gesture(gesture_name):
    """
    يتأكد من الـ gesture و يسجل كل حاجة في الـ log سواء صح أو غلط
    """
    try:
        if gesture_name in known_gestures:
            logger.info(f"Gesture detected correctly: {gesture_name}")
            
        else:
            logger.warning(f"Gesture attempted but not recognized: {gesture_name}")
            
    except Exception as e:
        logger.exception(f"Exception occurred while handling gesture '{gesture_name}': {e}")

#                        مثال على الاستخدام 
if __name__ == "__main__":
    gestures_to_test = ["hand right", "hand left", "hand up"]

    for gesture in gestures_to_test:
        handle_gesture(gesture)
