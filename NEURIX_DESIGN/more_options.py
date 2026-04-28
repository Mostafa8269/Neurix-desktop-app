from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont, QPixmap, QCursor
import os
import sys         
import subprocess
import cv2
import mediapipe as mp
import math
import pyautogui

# إيقاف خاصية الأمان عشان الماوس يتحرك بحرية تامة
pyautogui.FAILSAFE = False

# --- 1. محرك الـ Air Click المعدل للرسم والسحب (Drag and Drop) ---
class AirClickThread(QThread):
    click_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
        self.was_pinched = False
        self.screen_width, self.screen_height = pyautogui.size()

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if not ret: continue
            
            frame = cv2.flip(frame, 1) # مرايا
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                lms = results.multi_hand_landmarks[0].landmark
                
                # إحداثيات السبابة (رقم 8) لتحريك الماوس
                index_finger = lms[8]
                mouse_x = int(index_finger.x * self.screen_width)
                mouse_y = int(index_finger.y * self.screen_height)
                
                # تحريك سهم الماوس في الويندوز
                pyautogui.moveTo(mouse_x, mouse_y, _pause=False)

                # حساب المسافة للقرصة (بين الإبهام والسبابة)
                dist = math.hypot(lms[4].x - lms[8].x, lms[4].y - lms[8].y)
                
                # --- منطق الرسم (الضغط والسحب) ---
                if dist < 0.04: # لو صباعينك لمسوا بعض (بدأت القرصة)
                    if not self.was_pinched:
                        pyautogui.mouseDown() # "اضغط" الماوس وخليه دايس
                        self.was_pinched = True
                
                elif dist > 0.06: # لو فتحت صباعينك (سبت القرصة)
                    if self.was_pinched:
                        pyautogui.mouseUp() # "ارفع" الماوس دلوقتي
                        self.was_pinched = False
                        self.click_signal.emit() # إشارة عشان أزرار PyQt تشتغل
            
            self.msleep(10)
        cap.release()

    def stop(self):
        self.running = False

# --- 2. نافذة واجهة المستخدم (التصميم) ---
class MoreOptionsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neurix - More Options")
        self.setFixedSize(1920, 1080)
        self.setStyleSheet("""
            QWidget { background-color: #1b2735; }
            QPushButton {
                background-color: #0044ff;
                color: white;
                border-radius: 10px;
                padding: 10px;
                font-size: 18px;
            }
            QPushButton:hover { background-color: #00ffff; color: black; }
        """)

        # إنشاء العناصر الرسومية
        self.init_ui()

        # تشغيل المحرك
        self.air_thread = AirClickThread()
        self.air_thread.click_signal.connect(self.handle_air_click)
        self.air_thread.start()

    def init_ui(self):
        # نص Rule Option
        self.label_rule_text = QLabel("Rule Option", self)
        self.label_rule_text.setStyleSheet("color: #0044ff; font-size: 24px; font-weight: bold; border: 2px solid white; border-radius: 5px; padding: 5px;")
        self.label_rule_text.setGeometry(510, 660, 200, 50)
        self.label_rule_text.setAlignment(Qt.AlignCenter)

        # أيقونة المسطرة
        self.icon_ruler = QLabel(self)
        pix_r = QPixmap("Rul_icon.png")
        if not pix_r.isNull():
            s_r = pix_r.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_ruler.setPixmap(s_r)
            self.icon_ruler.setFixedSize(s_r.size())
        self.icon_ruler.move(460, 350)
        self.icon_ruler.setCursor(Qt.PointingHandCursor)
        self.icon_ruler.mousePressEvent = self.open_ruler

        # نص Scan_3D
        self.label_scan_text = QLabel("Scan_3D", self)
        self.label_scan_text.setStyleSheet("color: #0044ff; font-size: 24px; font-weight: bold; border: 2px solid white; border-radius: 5px; padding: 5px;")
        self.label_scan_text.setGeometry(1225, 640, 250, 50)
        self.label_scan_text.setAlignment(Qt.AlignCenter)

        # أيقونة الـ Scan
        self.icon_scan = QLabel(self)
        pix_s = QPixmap("can_3D.png")
        if not pix_s.isNull():
            s_s = pix_s.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_scan.setPixmap(s_s)
            self.icon_scan.setFixedSize(s_s.size())
        self.icon_scan.move(1200, 330)
        self.icon_scan.setCursor(Qt.PointingHandCursor)
        self.icon_scan.mousePressEvent = self.open_scan_3d

        # زرار العودة
        self.btn_close = QPushButton("Back to Home", self)
        self.btn_close.setGeometry(1670, 950, 200, 50)
        self.btn_close.clicked.connect(self.close)

    def handle_air_click(self):
        # الكليك العادي للأزرار داخل صفحة المور
        pos = QCursor.pos()
        widget = QApplication.widgetAt(pos)
        if widget:
            if widget == self.icon_ruler: self.open_ruler(None)
            elif widget == self.icon_scan: self.open_scan_3d(None)
            elif isinstance(widget, QPushButton): widget.click()

    def open_ruler(self, event):
        self.run_process("rule_option.py")

    def open_scan_3d(self, event):
        self.run_process("Scan_3D.py")

    def run_process(self, file_name):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            p = os.path.join(current_dir, file_name)
            if os.path.exists(p):
                subprocess.Popen([sys.executable, p], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        except Exception as e:
            print(f"Error: {e}")

    def closeEvent(self, event):
        self.air_thread.stop()
        self.air_thread.wait()
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Times New Roman", 150, QFont.Bold))
        painter.setPen(QColor(0, 255, 255, 20))
        painter.drawText(self.rect(), Qt.AlignCenter, "N")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MoreOptionsWindow()
    window.showFullScreen()
    sys.exit(app.exec_())