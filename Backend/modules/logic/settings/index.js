 from app_logging import logger
from command_router import route_command

def run_logic():
    logger.info("SETTINGS logic run triggered")
    route_command("settings")
