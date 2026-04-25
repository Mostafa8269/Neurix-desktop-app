from PyQt5.QtWidgets import QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QFont, QPixmap
import os
import sys        
import subprocess 

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

        # --- نص "Rule Option" فوق المسطرة ---
        self.label_rule_text = QLabel("Rule Option", self)
        self.label_rule_text.setStyleSheet("""
    QLabel {
        color: #0044ff; 
        font-size: 24px; 
        font-weight: bold;
        border: 2px solid white; 
        border-radius: 5px;
        padding: 5px;
        background-color: transparent;
    }
""")
        # نقوم بوضع النص فوق الأيقونة (الأيقونة عند 261، نضع النص عند 220 مثلاً)
        # العرض 200 ليناسب عرض الأيقونة ويكون في المنتصف
        self.label_rule_text.setGeometry(510, 660, 200, 50) 
        self.label_rule_text.setAlignment(Qt.AlignCenter)

        # --- أيقونة الـ Rule (المسطرة) ----
        self.icon_ruler = QLabel(self)
        pix_r = QPixmap("Rul_icon.png")
        if not pix_r.isNull():
            s_r = pix_r.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)#تكبير الايقونه
            self.icon_ruler.setPixmap(s_r)
            self.icon_ruler.setFixedSize(s_r.size())
        
        self.icon_ruler.move(460, 350)#موضع الايقونه
        self.icon_ruler.setCursor(Qt.PointingHandCursor)
        self.icon_ruler.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.icon_ruler.mousePressEvent = self.open_ruler # بتفتح ملف الـ rule

        # --- نص "Scan_3D" فوق أيقونة الـ Scan ---
        self.label_scan_text = QLabel("Scan_3D", self)
        self.label_scan_text.setStyleSheet("""
            QLabel {
                color: #0044ff; 
                font-size: 24px; 
                font-weight: bold;
                border: 2px solid white; 
                border-radius: 5px;
                padding: 5px;
            }
        """)
        # بما أن الأيقونة عند 1200، نضع النص عند 1175 ليتوسطها (بسبب زيادة عرض البرواز لـ 250)
        self.label_scan_text.setGeometry(1225, 640, 250, 50) 
        self.label_scan_text.setAlignment(Qt.AlignCenter)
        # --- أيقونة الـ Scan_3D (الجديدة) ---
        self.icon_scan = QLabel(self)
        pix_s = QPixmap("can_3D.png")
        if not pix_s.isNull():
            s_s = pix_s.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_scan.setPixmap(s_s)
            self.icon_scan.setFixedSize(s_s.size())
        
        self.icon_scan.move(1200, 330) # مكانها فوق الـ IX
        self.icon_scan.setCursor(Qt.PointingHandCursor)
        self.icon_scan.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.icon_scan.mousePressEvent = self.open_scan_3d # بتفتح ملف الـ scan

        # زرار العودة
        self.btn_close = QPushButton("Back to Home", self)
        self.btn_close.setGeometry(1670, 950, 200, 50)
        self.btn_close.clicked.connect(self.close)

    # دالة المسطرة (شغالة زي ما هي)
    def open_ruler(self, event):
        self.run_process("rule_option.py")

    # دالة الـ 3D Scan (الجديدة)
    def open_scan_3d(self, event):
        self.run_process("Scan_3D.py")

    # دالة التشغيل المستقلة
    def run_process(self, file_name):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            p = os.path.join(current_dir, file_name)
            if os.path.exists(p):
                subprocess.Popen([sys.executable, p], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            else:
                print(f"File not found: {p}")
        except Exception as e:
            print(f"Error: {e}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Times New Roman", 150, QFont.Bold))
        painter.setPen(QColor(0, 255, 255, 20))
        painter.drawText(self.rect(), Qt.AlignCenter, "N")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.close()