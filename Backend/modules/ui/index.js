import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
import gui_controller
from app_logging import logger  

class UI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Neurix")
        self.setGeometry(100, 100, 400, 300)
        logger.info("UI initialized: Neurix window created")

        layout = QVBoxLayout()

        # إنشاء الأزرار
        btn_view = QPushButton("View")
        btn_new = QPushButton("New")
        btn_settings = QPushButton("Settings")
        btn_more = QPushButton("More")

        # ربط الأزرار بالـ gui_controller مع تسجيل كل حدث
        btn_view.clicked.connect(lambda: self.handle_button("View"))
        btn_new.clicked.connect(lambda: self.handle_button("New"))
        btn_settings.clicked.connect(lambda: self.handle_button("Settings"))
        btn_more.clicked.connect(lambda: self.handle_button("More"))

        layout.addWidget(btn_view)
        layout.addWidget(btn_new)
        layout.addWidget(btn_settings)
        layout.addWidget(btn_more)

        self.setLayout(layout)

    def handle_button(self, button_name):
    
        logger.info(f"Button clicked in UI: {button_name}")
        gui_controller.button_clicked(button_name)

#                        تنفيذ التطبيق 
if __name__ == "__main__":
    try:
        logger.info("Starting UI application")
        app = QApplication(sys.argv)
        window = UI()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.exception(f"Exception occurred in UI: {e}") 
