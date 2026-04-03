from database import connect_db
import command_router
from app_logging import logger 

gesture_commands = {
    "hand_up": "new",
    "swipe_left": "view",
    "swipe_right": "settings",
    "fist": "exit",
    "open_hand": "more"
}

def add_design(name):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO designs (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        logger.info(f"Design '{name}' added to database")
    except Exception as e:
        logger.error(f"Failed to add design '{name}': {e}")

def get_designs():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM designs")
        data = cursor.fetchall()
        conn.close()
        logger.info(f"Fetched {len(data)} designs from database")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch designs: {e}")
        return []

def process_gesture(gesture, extra_data=None):
    if gesture in gesture_commands:
        command = gesture_commands[gesture]
        logger.info(f"Gesture recognized: '{gesture}' → executing command '{command}'")
        execute_command(command, extra_data)
    else:
        logger.warning(f"Gesture not recognized: '{gesture}'")

def execute_command(command, extra_data=None):
    if command == "new":
        add_design(extra_data or "Test Design")
        logger.info("Executed 'new' command via gesture")
    elif command == "view":
        designs = get_designs()
        logger.info(f"Executed 'view' command via gesture → Designs: {designs}")
    elif command == "settings":
        logger.info("Executed 'settings' command via gesture")
    elif command == "more":
        logger.info("Executed 'more' command via gesture")
    elif command == "exit":
        logger.info("Executed 'exit' command → Exiting program")
        exit()
