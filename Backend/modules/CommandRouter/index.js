import gui_controller
from backend import add_design, get_designs
from app_logging import logger  

def route_command(command, extra_data=None):


    if command == "new":
        # تنفيذ في الباك
        add_design(extra_data or "Test Design")
        logger.info(f"'new' command executed → Design added: {extra_data or 'Test Design'}")

        # فتح الواجهة
        gui_controller.open_new_design()
        logger.info("GUI opened for new design")

    elif command == "view":
        designs = get_designs()
        logger.info(f"'view' command executed → Designs: {designs}")

        gui_controller.open_view_design()
        logger.info("GUI opened to view designs")

    elif command == "settings":
        logger.info("'settings' command executed")
        gui_controller.open_settings()
        logger.info("GUI opened for settings")

    elif command == "more":
        logger.info("'more' command executed")
        gui_controller.open_more_options()
        logger.info("GUI opened for more options")

    elif command == "exit":
        logger.info("'exit' command executed → Exiting application")
        gui_controller.exit_app()
