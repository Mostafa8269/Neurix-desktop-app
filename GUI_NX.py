import sys #مكتبه تشغيل البرنامج واغلاقه
import random # خاصه بالشهب والنجوم
import os # مدير البرنامج
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGraphicsDropShadowEffect # المكتبه الرئيسيه
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer, QRectF, QRect # الاستدعاءات الخاصه
from PyQt5.QtGui import QColor, QImage, QPainter, QRadialGradient, QPen, QFont, QLinearGradient

class SpaceButton(QPushButton): #كلاس خاص لازرار وحجمها والدوائر
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(230, 230)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(30)
        self.shadow.setColor(QColor(0, 255, 255, 150))
        self.setGraphicsEffect(self.shadow)

    def paintEvent(self, event): # دالة رسم الدوائر والالوان
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect())
        
        grad = QRadialGradient(rect.center().x(), rect.center().y(), rect.width()/2)
        grad.setColorAt(0, QColor(80, 80, 90))
        grad.setColorAt(0.7, QColor(20, 20, 30))
        grad.setColorAt(1, Qt.black)
        painter.setBrush(grad)
        painter.setPen(QPen(QColor(0, 255, 255, 100), 2))
        painter.drawEllipse(rect.adjusted(2, 2, -2, -2))
        
        highlight = QLinearGradient(0, 0, 0, rect.height())
        highlight.setColorAt(0, QColor(255, 255, 255, 100))
        highlight.setColorAt(0.5, Qt.transparent)
        painter.setBrush(highlight)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(rect.width()*0.2), int(rect.height()*0.1), int(rect.width()*0.6), int(rect.height()*0.3))

        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Times New Roman", 24, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())

class MainWindow(QMainWindow):# كلاس الللوجو
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.bg_image = QImage("Logo.png.jpeg")
        
        self.stars = [[random.randint(0, 2500), random.randint(0, 1500), random.random()] for _ in range(150)]
        self.meteors = [[random.randint(500, 2000), random.randint(0, 600), random.randint(10, 25)] for _ in range(5)]
        
        # زر المركز N يحتوي علي قطر الدائره الخاصه بزر N والخط والمقاس
        self.main_btn = QPushButton("N", self.central_widget)
        self.main_btn.setFixedSize(230, 230)
        self.main_btn.setStyleSheet("""
            QPushButton {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.6, fx:0.5, fy:0.5, stop:0 #a0cfff, stop:1 #ffffff);
                color: #0044ff;
                border: 8px solid #00ffff;
                border-radius: 99px;
                font-size: 120px;
                font-family: "Times New Roman";
                font-weight: bold;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(160, 207, 255, 180))
        self.main_btn.setGraphicsEffect(shadow)

        # إعداد الأزرار الجانبية
        self.btns_list = [
            SpaceButton("New\nDesign", self.central_widget),
            SpaceButton("View\nDesign", self.central_widget),
            SpaceButton("Settings", self.central_widget),
            SpaceButton("More\nOptions", self.central_widget)
        ]
        
        self.btns_list[0].clicked.connect(lambda: self.run_logic("logic_new.py"))
        self.btns_list[1].clicked.connect(lambda: self.run_logic("logic_view.py"))
        self.btns_list[2].clicked.connect(lambda: self.run_logic("logic_settings.py"))
        self.btns_list[3].clicked.connect(lambda: self.run_logic("logic_more.py"))

        for b in self.btns_list: b.hide()
        self.menu_open = False
        self.main_btn.clicked.connect(self.toggle_menu)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_space)
        self.timer.start(30)
        
        self.showFullScreen()
        # تحديث الأنيميشن بعد ما الشاشة تفتح بالكامل
        QTimer.singleShot(100, self.setup_pulse)

    def setup_pulse(self):
        """إعداد نبض الزرار N بناءً على مكانه الحالي في السنتر"""
        self.pulse_anim = QPropertyAnimation(self.main_btn, b"geometry")
        self.pulse_anim.setDuration(800)
        self.pulse_anim.setLoopCount(-1)
        self.pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        rect = self.main_btn.geometry()
        c = rect.center()
        w, h = 175, 175
        
        small = QRect(c.x()-w//2, c.y()-h//2, w, h)
        big = QRect(c.x()-(w+15)//2, c.y()-(h+15)//2, w+15, h+15)
        
        self.pulse_anim.setKeyValueAt(0, small)
        self.pulse_anim.setKeyValueAt(0.5, big)
        self.pulse_anim.setKeyValueAt(1, small)
        self.pulse_anim.start()

    def resizeEvent(self, event):
        center = self.rect().center()
        self.main_btn.move(center.x() - 87, center.y() - 87)
        if hasattr(self, 'pulse_anim'): 
            self.pulse_anim.stop()
            self.setup_pulse()
        super().resizeEvent(event)

    def toggle_menu(self):
        if not self.menu_open:
            self.update_positions(animate=True)
            self.menu_open = True
        else:
            for b in self.btns_list: b.hide()
            self.menu_open = False

    def update_positions(self, animate=False):
        center = self.rect().center()
        ox, oy = 300, 220 # مسافات الازرار الجانبيه
        
        pos = [
            (center.x()-ox-87, center.y()-oy-87), (center.x()-ox-87, center.y()+oy-87),
            (center.x()+ox-87, center.y()-oy-87), (center.x()+ox-87, center.y()+oy-87)#ابعاد الازرار عن بعضها
        ]

        self.anims = [] 
        for i, btn in enumerate(self.btns_list):
            target = QPoint(int(pos[i][0]), int(pos[i][1]))
            btn.show()
            if animate:
                a = QPropertyAnimation(btn, b"pos")
                a.setDuration(600)
                a.setStartValue(self.main_btn.pos())
                a.setEndValue(target)
                a.setEasingCurve(QEasingCurve.OutBack)
                self.anims.append(a)
                a.start()
            else:
                btn.move(target)

    def run_logic(self, file_name):
        print(f"[DEBUG]: Executing: {file_name}")
        if os.path.exists(file_name):
            os.system(f"python {file_name}")
        else:
            print(f"[ERROR]: {file_name} not found!")

    def update_space(self):
        for i in range(len(self.meteors)):
            self.meteors[i][0] -= self.meteors[i][2]
            self.meteors[i][1] += self.meteors[i][2] * 0.5
            if self.meteors[i][0] < -200:
                self.meteors[i] = [2500, random.randint(0, 600), random.randint(10, 25)]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.bg_image.isNull():
            painter.drawImage(self.rect(), self.bg_image)
        for s in self.stars:
            painter.setPen(QPen(QColor(255, 255, 255, random.randint(150, 255)), 2))
            painter.drawPoint(int(s[0]), int(s[1]))
        for m in self.meteors:
            grad = QLinearGradient(m[0], m[1], m[0]+120, m[1]-60)
            grad.setColorAt(0, QColor(0, 255, 255, 200))
            grad.setColorAt(1, Qt.transparent)
            painter.setPen(QPen(grad, 3))
            painter.drawLine(int(m[0]), int(m[1]), int(m[0]+100), int(m[1]-50))

    def keyPressEvent(self, event):# تفعيل زرار ESc
        if event.key() == Qt.Key_Escape: self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())