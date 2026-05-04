import sys # مكتبه تشغيل البرنامج واغلاقه
import random # خاصه بالشهب والنجوم
import os # مدير البرنامج
from multiprocessing import Process
from viewDesgin import Viewer
from more_options import MoreOptionsWindow # استدعاء الموديول الجديد
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                             QGraphicsDropShadowEffect, QVBoxLayout, QHBoxLayout, 
                             QLabel, QCheckBox, QStackedWidget, QFrame, QGridLayout, 
                             QSpacerItem, QSizePolicy, QSlider, QComboBox, QProgressBar)
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QTimer, QRectF, QRect # الاستدعاءات الخاصه
from PyQt5.QtGui import QColor, QImage, QPainter, QRadialGradient, QPen, QFont, QLinearGradient, QPixmap
import screen_brightness_control as sbc #مكتبه التحكم في السطوع
from ctypes import cast, POINTER #مكتبه تعامل مع مؤشرات النظام
from comtypes import CLSCTX_ALL #دا كدا يبقي تست لو ضيفت صوت عشان دا اللي بيتجاوب مع صوت الوييندوزcom
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume #مهمه عشان لما نضيف الصوت
import psutil #مهمه جدا دي بتراقب الرام والمعالج بتراقب الجهاز
from PyQt5.QtWidgets import * #دي طبعا لعناصر الواجهه
from PyQt5.QtCore import *#فيها الحاجات الاساسيه زي ال الشهب ونجوم وكدا
from PyQt5.QtGui import *# دا النقاش بتاعي
from pygame import mixer
import cv2
import mediapipe as mp
import math
import pyautogui
# لإيقاف خاصية الأمان عشان الماوس يتحرك بحرية في كل الشاشة
pyautogui.FAILSAFE = False

from more_options import MoreOptionsWindow
mixer.init() # تشغيل نظام الصوت
mixer.init() # تشغيل نظام الصوت
sound_enabled = True  # متغير عالمي للتحكم في الصوت (True = شغال)

def play_home_sound():
    global sound_enabled
    if not sound_enabled: # لو الصوت معطل، اخرج من الدالة ولا تفعل شيء
        return
        
    try:
        if os.path.exists('home.wav'):
            sound = mixer.Sound('home.wav')
            sound.play()
    except Exception as e:
        print(f"Error playing sound: {e}")


def launch_panda():
    from viewDesgin import Viewer
    app = Viewer()
    app.run()

def New_panda():
    # هنا بنشغل الكلاس اللي أنت عملته للـ 3D
    # لو كود الباندا في ملف اسمه new_design.py
    from new_design import ModularDesignApp 
    app = ModularDesignApp()
    app.run()    

class SpaceButton(QPushButton): #دا كلاس الازرار الجانبيه تم نقل الكلاس دا فوق بسبب عطل بسيط في قراءه الاكلاس
    def __init__(self, text, parent=None):#داله البدايه مهمه دي اللي هيبقي فيها الحجم والشكل
        super().__init__(text, parent)
        self.setFixedSize(230, 230)#حجم الزر الجانبي
        self.setCursor(Qt.PointingHandCursor)#دي عشان خاطر لما اتوجهه نحو اي زر شكل الماوس يتغير فابعرف اني واقف علي الزر
        self.setStyleSheet("background: transparent; border: none;")#هنا بقول خلص الزر دا هيتم رسمه دا امر مني
        
        self.shadow = QGraphicsDropShadowEffect()#ابتداء من الظل الخارجي
        self.shadow.setBlurRadius(30)#نعومة الظل ملحوظه كل م الرقم يزيد يكون انعم واوسع
        self.shadow.setColor(QColor(0, 255, 255, 150))#اللون الازرق اللي خلف الازرار لون سماوي شفاف
        self.setGraphicsEffect(self.shadow)#هنا بقي ربط الزر بالظل اللي وراه

    def paintEvent(self, event):#نتعود علي الداله دي انها فرشة الرسم بتاعتي
        painter = QPainter(self)#بجهز الفرشه
        painter.setRenderHint(QPainter.Antialiasing)#بتخلي الدايره بتاعتي ناعمه
        rect = QRectF(self.rect())#دي بتجيب مساحه الزر 230*230
        
        grad = QRadialGradient(rect.center().x(), rect.center().y(), rect.width()/2)#دي بتعمل التدرج الدائري هما اللون بيغمق
        grad.setColorAt(0, QColor(80, 80, 90))#اللون منور من النص
        grad.setColorAt(0.7, QColor(20, 20, 30))#غامق عند الاطراف
        grad.setColorAt(1, Qt.black)#اسود من برا
        painter.setBrush(grad)#رسم حدود الدائره الاطارات
        painter.setPen(QPen(QColor(0, 255, 255, 100), 2))#اطار سماوي رفيع
        painter.drawEllipse(rect.adjusted(2, 2, -2, -2))#رسم الدائره بقا
        
        highlight = QLinearGradient(0, 0, 0, rect.height())#دي بقا اللي تضيف للزر اللمعه 
        highlight.setColorAt(0, QColor(255, 255, 255, 100))#للمعه فوق الزر
        highlight.setColorAt(0.5, Qt.transparent)#من اسفل الزر اللمعه تختفي
        painter.setBrush(highlight)#اللمعه تكون smooth
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(rect.width()*0.2), int(rect.height()*0.1), int(rect.width()*0.6), int(rect.height()*0.3))#المضيئه معادله لتسهيل حسابات الدوائر

        painter.setPen(QColor(255, 255, 255))#رسم النص
        painter.setFont(QFont("Times New Roman", 24, QFont.Bold))#نوع الخط وحجمه ومقاسه
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())#عشان النص يبقي في المنتصف

class SettingsWindow(QWidget):#الكلاس الخاص بالاعدادات
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neurix Settings")
        self.setFixedSize(1280, 850) 
        
        # --- Stylesheet ---
        self.setStyleSheet("""
            QWidget { background-color: #050510; color: #00ffff; font-family: 'Segoe UI', sans-serif; }
            #Sidebar { background-color: #0a0a1a; border-right: 2px solid #00ffff; }
            #ContentArea { background-color: #0f0f1a; border-radius: 20px; margin: 15px; }
            QLabel#Title { font-size: 42px; font-weight: bold; color: #00ffff; margin-bottom: 25px; }
            QLabel#SubTitle { font-size: 28px; font-weight: bold; color: #a0cfff; margin-top: 25px; margin-bottom: 15px; }
            #ContentArea QLabel { font-size: 22px; color: #e0e0e0; }
            QPushButton#MenuBtn {
                background-color: transparent; border: 1px solid #0044ff; border-radius: 12px;
                padding: 18px; font-size: 24px; color: white; text-align: left;
            }
            QPushButton#MenuBtn:hover { background-color: #00ffff; color: black; }
            QPushButton#MenuBtn:checked { background-color: #0044ff; border: 2px solid #00ffff; }
            QSlider::groove:horizontal { border: 1px solid #0044ff; height: 12px; background: #0a0a1a; border-radius: 6px; }
            QSlider::handle:horizontal {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, stop:0 #ffffff, stop:1 #00ffff);
                border: 2px solid #0044ff; width: 28px; height: 28px; margin: -9px 0; border-radius: 14px;
            }
            QCheckBox::indicator { width: 65px; height: 32px; border-radius: 16px; }
            QCheckBox::indicator:unchecked { background-color: #1a1a2e; border: 2px solid #ff0055; }
            QCheckBox::indicator:checked { background-color: #00ffff; border: 2px solid #0044ff; }
            QComboBox { background-color: #1a1a2e; border: 2px solid #00ffff; border-radius: 8px; padding: 10px; font-size: 22px; color: white; }
            QProgressBar { border: 2px solid #00ffff; border-radius: 10px; text-align: center; height: 25px; font-size: 18px; color: white; }
            QProgressBar::chunk { background-color: #0044ff; border-radius: 8px; }
        """)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = QFrame(); self.sidebar.setObjectName("Sidebar"); self.sidebar.setFixedWidth(320)
        layout_side = QVBoxLayout(self.sidebar); layout_side.setContentsMargins(20, 50, 20, 20); layout_side.setSpacing(20)

        self.btn_app = QPushButton("Appearance 🔑"); self.btn_perf = QPushButton("Performance ⚡")
        self.btn_gest = QPushButton("Gestures ✋"); self.btn_about = QPushButton("About ℹ️")

        self.menu_buttons = [self.btn_app, self.btn_perf, self.btn_gest, self.btn_about]
        for btn in self.menu_buttons:
            btn.setObjectName("MenuBtn"); btn.setCheckable(True); layout_side.addWidget(btn)
        layout_side.addStretch()

        # Content Area
        self.content_container = QFrame(); self.content_container.setObjectName("ContentArea")
        self.pages = QStackedWidget()
        layout_cont = QVBoxLayout(self.content_container)
        layout_cont.setContentsMargins(0, 0, 0, 0)
        
        # إضافة الصفحات للـ Layout العلوي
        layout_cont.addWidget(self.pages)

        # إنشاء الصفحات (الآن الدالة لا تحتوي على أزرار داخلية)
        self.create_pages()

        # --- إضافة أزرار التحكم الثابتة بالأسفل (Global Buttons) ---
        btn_container = QHBoxLayout()
        btn_container.setContentsMargins(0, 10, 40, 25) # هوامش لضبط المكان
        btn_container.addStretch() # دفع الأزرار لليمين

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setFixedSize(140, 55)
        self.reset_btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent; color: #ff0055; font-size: 20px; 
                font-weight: bold; border: 2px solid #ff0055; border-radius: 10px;
            }
            QPushButton:hover { background-color: #ff0055; color: white; }
        """)

        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setFixedSize(180, 55)
        self.save_btn.setStyleSheet("""
            QPushButton { 
                background-color: #0044ff; color: white; font-size: 20px; 
                font-weight: bold; border-radius: 10px;
            }
            QPushButton:hover { background-color: #00ffff; color: black; }
        """)

        btn_container.addWidget(self.reset_btn)
        btn_container.addWidget(self.save_btn)
        
        # إضافة حاوية الأزرار أسفل الـ StackedWidget مباشرة
        layout_cont.addLayout(btn_container)

        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_container)

        # ربط التنقل
        self.btn_app.clicked.connect(lambda: self.switch_page(0))
        self.btn_perf.clicked.connect(lambda: self.switch_page(1))
        self.btn_gest.clicked.connect(lambda: self.switch_page(2))
        self.btn_about.clicked.connect(lambda: self.switch_page(3))
        self.switch_page(0)

        # --- ربط الإشارات (Signals) لتفعيل الأوامر ---
        self.bright_slide.valueChanged.connect(self.set_brightness)
        self.vol_slide.valueChanged.connect(self.set_volume)
        self.sound_toggle.toggled.connect(self.update_internal_sound)
        self.res_box.activated.connect(self.change_resolution)
        self.mode_box.activated.connect(self.change_system_mode)
        self.save_btn.clicked.connect(self.apply_all_changes)
        
        # تايمر تحديث الـ Hardware Monitoring
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_hardware_stats)
        self.stats_timer.start(1000)
        # ربط زرار الـ Reset بدالة المسح
        self.reset_btn.clicked.connect(self.reset_to_defaults)

    def create_pages(self):
        # --- 1. صفحة Appearance ---
        p1 = QWidget(); l1 = QVBoxLayout(p1)
        l1.setContentsMargins(40, 40, 40, 40)
        l1.addWidget(QLabel("Appearance", objectName="Title"))
        
        l1.addWidget(QLabel("Resolution / Scale", objectName="SubTitle"))
        self.res_box = QComboBox()
        self.res_box.addItems(["1920x1080 (Recommended)", "1280x720", "1024x768"])
        l1.addWidget(self.res_box)

        l1.addWidget(QLabel("Brightness Control", objectName="SubTitle"))
        self.bright_slide = QSlider(Qt.Orientation.Horizontal)
        self.bright_slide.setRange(0, 100); self.bright_slide.setValue(70)
        l1.addWidget(self.bright_slide)

        l1.addWidget(QLabel("Sound System", objectName="SubTitle"))
        sound_container = QFrame(); sound_container.setStyleSheet("background: #161625; border-radius: 20px; padding: 20px;")
        sound_lay = QHBoxLayout(sound_container)
        self.sound_toggle = QCheckBox("On/Off Switch"); self.sound_toggle.setChecked(True)
        self.vol_slide = QSlider(Qt.Orientation.Horizontal); self.vol_slide.setRange(0, 100); self.vol_slide.setValue(50)
        sound_lay.addWidget(self.sound_toggle); sound_lay.addSpacing(40)
        sound_lay.addWidget(QLabel("Volume:")); sound_lay.addWidget(self.vol_slide)
        l1.addWidget(sound_container)
        
        l1.addStretch() # دفع المحتوى للأعلى (الأزرار ستكون في الـ Layout الخارجي)
        self.pages.addWidget(p1)

        # --- 2. صفحة Performance (التصميم المنظم) ---
        p2 = QWidget(); l2 = QVBoxLayout(p2)
        l2.setContentsMargins(40, 40, 40, 40); l2.setSpacing(15)
        l2.addWidget(QLabel("Performance", objectName="Title"))
        
        l2.addWidget(QLabel("System Mode", objectName="SubTitle"))
        self.mode_box = QComboBox()
        self.mode_box.addItems(["Low Power", "Balanced", "High Performance 🔥"])
        l2.addWidget(self.mode_box)

        l2.addWidget(QLabel("Hardware Monitoring", objectName="SubTitle"))
        l2.addWidget(QLabel("CPU Usage:")); self.cpu_bar = QProgressBar(); l2.addWidget(self.cpu_bar)
        l2.addWidget(QLabel("RAM Usage:")); self.ram_bar = QProgressBar(); l2.addWidget(self.ram_bar)

        l2.addWidget(QLabel("Camera Settings", objectName="SubTitle"))
        cam_grid = QGridLayout()
        self.fps_box = QComboBox(); self.fps_box.addItems(["30 FPS", "60 FPS"])
        self.res_cam = QComboBox(); self.res_cam.addItems(["720p", "1080p"])
        cam_grid.addWidget(QLabel("FPS:"), 0, 0); cam_grid.addWidget(self.fps_box, 0, 1)
        cam_grid.addWidget(QLabel("Quality:"), 0, 2); cam_grid.addWidget(self.res_cam, 0, 3)
        l2.addLayout(cam_grid)
        
        l2.addStretch() 
        self.pages.addWidget(p2)
        
        # --- 3. صفحة Gestures (التحكم بالإشارات) ---
        p3 = QWidget(); l3 = QVBoxLayout(p3)
        l3.setContentsMargins(40, 40, 40, 40); l3.setSpacing(10)#محاذاه المسافات
        
        l3.addWidget(QLabel("Gestures Mapping", objectName="Title"))#العنوان الاول

        special_title = QLabel("Special Signals for controlling the program.")#عنوان جانبي اخر
        special_title.setStyleSheet("font-size: 32px; font-weight: bold; color: #a0cfff; margin-bottom: 15px;")#مقاس الخط وسمكه 
        l3.addWidget(special_title)

        gestures_grid = QGridLayout(); gestures_grid.setSpacing(10)
        gestures_names = ["Air_Click", "Rotation", "Zoom In & Zoom Out", "Move"]
        for i, name in enumerate(gestures_names, 1):#دي الحسابات اللي عملها بمساعده ال AI لمحاذاه الكلمات
            row = (i - 1) // 2; col = (i - 1) % 2 * 2
            lbl = QLabel(f"{i}) {name}")
            lbl.setStyleSheet("font-size: 28px; color: #e0e0e0; font-weight: 500;")
            gestures_grid.addWidget(lbl, row, col)
        l3.addLayout(gestures_grid)

        self.hand_landmark_check = QCheckBox("Show hand landmark")
        self.hand_landmark_check.setStyleSheet("""
            QCheckBox { font-size: 28px; color: #00ffff; font-weight: bold; margin-top: 10px; }
            QCheckBox::indicator { width: 30px; height: 30px; }
        """)
        l3.addWidget(self.hand_landmark_check)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #0044ff; min-height: 2px; margin-top: 10px;")
        l3.addWidget(line)

        how_to_label = QLabel("How to use signal")
        how_to_label.setStyleSheet("font-size: 34px; font-weight: bold; color: #ffffff; text-decoration: underline; margin-top: 5px;")
        l3.addWidget(how_to_label)

        instructions_style = "font-size: 20px; color: #cccccc; line-height: 1.5; margin-left: 10px;"
        title_style = "font-size: 24px; color: #00ffff; font-weight: bold; margin-top: 10px;"

        l3.addWidget(QLabel("1) Air_Click:", styleSheet=title_style))
        air_desc = QLabel("We use Air Click to click on things. To make a click, we must use our hand in this way: the index finger should be raised and the thumb parallel to the index finger. When clicking, we place the index finger on the thumb.")
        air_desc.setWordWrap(True); air_desc.setStyleSheet(instructions_style)
        l3.addWidget(air_desc)
        
        l3.addWidget(QLabel("-" * 120, styleSheet="color: #1a1a2e;"))

        l3.addWidget(QLabel("2) Rotation:", styleSheet=title_style))
        rot_desc = QLabel("Use rotation when the hand is closed and only the index finger is raised.")
        rot_desc.setWordWrap(True); rot_desc.setStyleSheet(instructions_style)
        l3.addWidget(rot_desc)

        l3.addWidget(QLabel("-" * 120, styleSheet="color: #1a1a2e;"))

        l3.addWidget(QLabel("Zoom In & Zoom out:", styleSheet=title_style))
        zoom_desc = QLabel("To zoom in and zoom out, we must form a circle with our thumb and forefinger. To zoom in, close the circle, and to zoom out, open the circle with the other three fingers raised.")
        zoom_desc.setWordWrap(True); zoom_desc.setStyleSheet(instructions_style)
        l3.addWidget(zoom_desc)

        l3.addWidget(QLabel("Move:", styleSheet=title_style))
        mov_desc = QLabel("To move anything, the hand must be in this position: the index, middle, and thumb fingers must be connected to move, and they must be separated to separate")
        mov_desc.setWordWrap(True); mov_desc.setStyleSheet(instructions_style)
        l3.addWidget(mov_desc)

        l3.addStretch()
        self.pages.addWidget(p3)

        # --- 4. صفحة About (التحديث الجديد) ---
        p4 = QWidget(); l4 = QVBoxLayout(p4)
        l4.setContentsMargins(50, 40, 50, 40); l4.setSpacing(10)

        # ستايلات الصفحة
        section_title_style = "font-size: 30px; font-weight: bold; color: #00ffff; margin-top: 10px;"
        info_label_style = "font-size: 22px; color: #e0e0e0; margin-left: 15px;"
        value_text_style = "font-size: 20px; color: #cccccc; line-height: 1.4; margin-left: 20px;"
        line_style = "background-color: #0044ff; min-height: 1px; margin-top: 5px; margin-bottom: 5px;"

        # العنوان الرئيسي
        l4.addWidget(QLabel("About NEURIX", objectName="Title"))

        # 1. Project Information
        l4.addWidget(QLabel("Project information:", styleSheet=section_title_style))
        l4.addWidget(QLabel("Project name:  Neurix – Vision-Based Touchless Interactive System", styleSheet=info_label_style))
        l4.addWidget(QLabel("Lead developer by:  NEURIX TEAM", styleSheet=info_label_style))
        l4.addWidget(QLabel("Version:  1.0.0", styleSheet=info_label_style))
        
        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setStyleSheet(line_style)
        l4.addWidget(line1)

        # 2. Project Vision
        l4.addWidget(QLabel("Project vision:", styleSheet=section_title_style))
        vision_txt = QLabel("*) To develop a scalable, fully integrated touchless interactive system that begins as a functional prototype and evolves into a professional-grade interactive device suitable for real-world deployment.")
        vision_txt.setWordWrap(True); vision_txt.setStyleSheet(value_text_style)
        l4.addWidget(vision_txt)

        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine); line2.setStyleSheet(line_style)
        l4.addWidget(line2)

        # 3. What Makes the Project Unique
        l4.addWidget(QLabel("What Makes the Project Unique:", styleSheet=section_title_style))
        unique_txt = QLabel("1) Full integration between hardware and software\n2) Built locally as a complete working system")
        unique_txt.setStyleSheet(value_text_style)
        l4.addWidget(unique_txt)

        line3 = QFrame(); line3.setFrameShape(QFrame.Shape.HLine); line3.setStyleSheet(line_style)
        l4.addWidget(line3)

        # 4. Project Goal
        l4.addWidget(QLabel("Project goal:", styleSheet=section_title_style))
        goal_txt = QLabel("1) This reduces design errors and simplifies the user experience.\n2) Ensure basic printability conditions automatically")
        goal_txt.setWordWrap(True); goal_txt.setStyleSheet(value_text_style)
        l4.addWidget(goal_txt)

        line4 = QFrame(); line4.setFrameShape(QFrame.Shape.HLine); line4.setStyleSheet(line_style)
        l4.addWidget(line4)

        # 5. Footer (Center Aligned)
        l4.addStretch()
        footer_txt = QLabel("With Neurix Your Hand - Your World")
        footer_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_txt.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ffff; font-style: italic; margin-bottom: 10px;")
        l4.addWidget(footer_txt)

        self.pages.addWidget(p4)

    # --- الدوال التنفيذية ---
    def set_brightness(self, value):
        try: sbc.set_brightness(value)
        except: pass
    
    def apply_all_changes(self):
    # 1. حفظ وتطبيق حالة الصوت
        global sound_enabled
        sound_enabled = self.sound_toggle.isChecked()
    
    # 2. تطبيق السطوع
        brightness_value = self.bright_slide.value()
        self.set_brightness(brightness_value)
    
    # 3. تطبيق مستوى الصوت (System Volume)
        volume_value = self.vol_slide.value()
        self.set_volume(volume_value)
    
    # 4. تطبيق الدقة (Resolution)
        self.change_resolution()
    
    # 5. رسالة تأكيد (اختياري)
    print("All changes saved and applied successfully!")
    # ممكن تقفل النافذة بعد الحفظ لو تحب:
    # self.close()
    
    def apply_global_resolution(self):
        res = self.res_cam.currentText()
        
        # 96 هو الـ DPI القياسي (720p تقريباً في الوضوح)
        # 120 أو 144 بيزود الدقة جداً (1080p وما فوق)
        
        if "1080p" in res:
            new_dpi = 144  # دقة عالية جداً ووضوح فائق
        else:
            new_dpi = 96   # دقة عادية
            
        # تطبيق الدقة على البرنامج بالكامل
        for widget in QApplication.allWidgets():
            widget.setLogicalDpiX(new_dpi)
            widget.setLogicalDpiY(new_dpi)
            
        # تحديث الواجهة لإجبار البرنامج على إعادة الرسم بالدقة الجديدة
        self.main_win.update()
        self.update()

    def set_volume(self, value):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(value / 100, None)
        except: pass

    def toggle_mute(self, state):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(not state, None)
        except: pass

    def change_resolution(self):
        res = self.res_box.currentText()
        if "1920x1080" in res: self.window().showFullScreen()
        else: self.window().showNormal(); self.window().resize(1280, 720)

    def update_hardware_stats(self):#عشان اشوف استهلاك الرام والمعالج الفعلي وانا شغال
        self.cpu_bar.setValue(int(psutil.cpu_percent()))
        self.ram_bar.setValue(int(psutil.virtual_memory().percent))

    def change_system_mode(self):#مسؤول عن الاضاءه
        print(f"Mode changed to: {self.mode_box.currentText()}")

    def switch_page(self, index):#انتقال من صفحه لاخري
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.menu_buttons): btn.setChecked(i == index)
    def reset_to_defaults(self):
        self.res_box.setCurrentIndex(0)
        self.bright_slide.setValue(70)
        self.sound_toggle.setChecked(True) # رجعناه True كوضع افتراضي
        self.vol_slide.setValue(50)
        self.mode_box.setCurrentIndex(1)
        self.fps_box.setCurrentIndex(0)
        self.res_cam.setCurrentIndex(0)
        self.hand_landmark_check.setChecked(False)
        print("Settings reset to defaults. Click Save to apply.")

        # 3. إعدادات Gestures
        self.hand_landmark_check.setChecked(False)    # إخفاء نقاط اليد افتراضياً
    
    def update_internal_sound(self, state):
        global sound_enabled
        sound_enabled = state
        print(f"Neurix Sound: {'ON' if state else 'OFF'}")
     
    def keyPressEvent(self, event):#زر ال الاغلاق 
        if event.key() == Qt.Key.Key_Escape: self.close()
class AirClickThread(QThread):
    click_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.was_pinched = False
        self.screen_width, self.screen_height = pyautogui.size()

    def run(self):
        # CAP_DSHOW بتخلي الكاميرا تفتح أسرع على ويندوز
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # معالجة الصورة
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                lms = results.multi_hand_landmarks[0].landmark
                index_finger = lms[8]
                thumb_finger = lms[4]

                # حساب المسافة بين طرف الإبهام وطرف السبابة
                dist = math.hypot(thumb_finger.x - index_finger.x, thumb_finger.y - index_finger.y)

                # --- منطق الضغط الذكي ---
                if dist < 0.04:  # حالة الضغط (Pinch)
                    if not self.was_pinched:
                        # 1. إرسال الإشارة للنقر فوراً
                        self.click_signal.emit()
                        self.was_pinched = True
                        print("🎯 Air Click Triggered!")
                    
                    # ملاحظة: هنا مش بنحدث mx و my فالموس "بيثبت" مكانه وقت الضغطة
                
                else:
                    # لو الصوابع بعدت عن بعض، رجع إمكانية الضغط وحرك الماوس عادي
                    if dist > 0.06:
                        self.was_pinched = False
                    
                    # تحريك الماوس بس في حالة "عدم الضغط" عشان نمنع النطرة
                    mx = int(index_finger.x * self.screen_width)
                    my = int(index_finger.y * self.screen_height)
                    
                    # _pause=False بتخلي الحركة سريعة ومن غير تأخير
                    pyautogui.moveTo(mx, my, _pause=False)
            
            # موازنة بين سرعة الاستجابة واستهلاك البروسيسور
            self.msleep(5) 
        
        # تنظيف الكاميرا بعد الخروج من اللوب
        cap.release()
        print("📷 Camera Released Successfully.")

    def stop(self):
        self.running = False

# --- 3. كلاس النافذة الرئيسية (MainWindow) ---
class MainWindow(QMainWindow):#الكلاس دا مسؤول عن انشاء النافذه والشهب والنجوم وتحميل الخلفيه وانشاء زر الN الاساسي
    def __init__(self):#مهمه لتشغيل ال نافذه
        super().__init__()#شغل اعدادات ال mainwindow
        self.central_widget = QWidget()#زي مانا عارف الQWidget دي بتتحط فيها كل العناصر اللي عايز اضيفها علي الواجهه
        self.setCentralWidget(self.central_widget)#ال Widget دي عمله زي الشنطه تمام فيها زر الN والحاجات دي
        self.bg_image = QImage("Logo.png.jpeg")#تحميل الخلفيه من الملف
        # --- داخل دالة __init__ ---
        self.monitor_timer = QTimer()
        self.p_3d = None
        self.p_new = None
        # ------------------------
        self.stars = [[random.randint(0, 2500), random.randint(0, 1500), random.random()] for _ in range(150)]#عمل النجوم وعددها 150 نجمه عشوائيه الاول نجوم افقيه والتاني راسي
        self.meteors = [[random.randint(500, 2000), random.randint(0, 600), random.randint(10, 25)] for _ in range(5)]#دا بقا الشهب 5شهب اول حاجه يبدا من نص الشاشه لليمين وبيحدد السرعه
        
        self.main_btn = QPushButton("N", self.central_widget)#زرار ال N الاساسي دا مركز الواجهه
        self.main_btn.setFixedSize(230, 230)#حجمه طبعا
        self.main_btn.setStyleSheet("""
            QPushButton {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.6, fx:0.5, fy:0.5, stop:0 #a0cfff, stop:1 #ffffff);
                color: #0044ff; border: 8px solid #00ffff; border-radius: 99px;
                font-size: 120px; font-family: "Times New Roman"; font-weight: bold;
            }
        """)#متصمم باستخدام ثانيااللون ازرق والاطار8بكس وقطر الدائره99 Qt css 1-bتدرج دائري عشان الزر يبقي مفتح من النص 

        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(40); shadow.setColor(QColor(160, 207, 255, 180))
        self.main_btn.setGraphicsEffect(shadow)

        self.btns_list = [
            SpaceButton("New\nDesign", self.central_widget),
            SpaceButton("View\nDesign", self.central_widget),
            SpaceButton("Settings", self.central_widget),
            SpaceButton("More\nOptions", self.central_widget)
        ]
        
        self.btns_list[0].clicked.connect(self.open_new_design)
        self.btns_list[1].clicked.connect(self.open_3d_viewer)
        self.btns_list[2].clicked.connect(self.open_settings)
        self.btns_list[3].clicked.connect(self.open_more_options)

        for btn in self.btns_list:
            btn.clicked.connect(play_home_sound)

        for b in self.btns_list: b.hide()
        self.menu_open = False
        self.settings_window = SettingsWindow()
        
        self.more_options_win = MoreOptionsWindow()
        self.main_btn.clicked.connect(self.toggle_menu)
        self.main_btn.clicked.connect(play_home_sound)
        
        self.timer = QTimer(); self.timer.timeout.connect(self.update_space); self.timer.start(30)
        
        self.showFullScreen()
        QTimer.singleShot(100, self.setup_pulse)
        # تشغيل محرك الـ Air Click
        self.air_thread = AirClickThread()
        self.air_thread.click_signal.connect(self.handle_air_click)
        self.air_thread.start()

    def handle_air_click(self):
        from PyQt5.QtCore import QEvent, Qt
        from PyQt5.QtGui import QMouseEvent
        
        # 1. تحديد مكان الماوس بدقة
        pos = QCursor.pos()
        widget = QApplication.widgetAt(pos)
        
        if widget:
            # 2. تحويل الإحداثيات من الشاشة لإحداثيات الـ Widget نفسه
            local_pos = widget.mapFromGlobal(pos)
            
            # 3. إنشاء حدث "ضغطة ماوس يسار" حقيقي
            press_event = QMouseEvent(
                QEvent.MouseButtonPress, 
                local_pos, 
                Qt.LeftButton, 
                Qt.LeftButton, 
                Qt.NoModifier
            )
            
            # 4. إنشاء حدث "ترك الماوس" (Release) عشان الضغطة تكتمل
            release_event = QMouseEvent(
                QEvent.MouseButtonRelease, 
                local_pos, 
                Qt.LeftButton, 
                Qt.LeftButton, 
                Qt.NoModifier
            )
            
            # 5. إرسال الأحداث للـ Widget مباشرة
            # دي بتخلي أي حاجة (زرار، قائمة، سلايدر) تحس إن فيه ماوس حقيقي داس عليها
            QApplication.sendEvent(widget, press_event)
            QApplication.sendEvent(widget, release_event)
            
            print(f"🔥 Force Click sent to: {widget.metaObject().className()}")

    def restart_main_gestures(self):
        """إعادة تشغيل تتبع اليد للواجهة الأساسية"""
        if not hasattr(self, 'air_thread') or not self.air_thread.isRunning():
            print("🔄 Resuming Main UI Gestures...")
            self.air_thread = AirClickThread()
            self.air_thread.click_signal.connect(self.handle_air_click)
            self.air_thread.start()

    def open_settings(self):
        self.settings_window.showMaximized()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def open_more_options(self):
        self.more_options_win.show()
        self.more_options_win.raise_()
        self.more_options_win.activateWindow()
        play_home_sound()

    def setup_pulse(self):
        self.pulse_anim = QPropertyAnimation(self.main_btn, b"geometry")
        self.pulse_anim.setDuration(800); self.pulse_anim.setLoopCount(-1); self.pulse_anim.setEasingCurve(QEasingCurve.InOutQuad)
        rect = self.main_btn.geometry(); c = rect.center(); w, h = 175, 175
        small = QRect(c.x()-w//2, c.y()-h//2, w, h); big = QRect(c.x()-(w+15)//2, c.y()-(h+15)//2, w+15, h+15)
        self.pulse_anim.setKeyValueAt(0, small); self.pulse_anim.setKeyValueAt(0.5, big); self.pulse_anim.setKeyValueAt(1, small)
        self.pulse_anim.start()

    def open_3d_viewer(self):
        print("🎬 Launching View Design...")
        
        # 1. حرر الكاميرا فوراً
        if hasattr(self, 'air_thread') and self.air_thread.isRunning():
            self.air_thread.stop()
            self.air_thread.wait() # مهم جداً عشان الكاميرا متعلقش

        # 2. شغل الفيو
        self.p_3d = Process(target=launch_panda)
        self.p_3d.start()
        
        # 3. راقب العملية عشان ترجع الكاميرا لما يقفل
        try: self.monitor_timer.timeout.disconnect()
        except: pass
        self.monitor_timer.timeout.connect(self.check_panda_status)
        self.monitor_timer.start(1000)

    def check_panda_status(self):
        if self.p_3d and not self.p_3d.is_alive():
            self.monitor_timer.stop()
            self.restart_main_gestures()

    def open_new_design(self):
        print("🎨 Launching New Design...")

        # 1. حرر الكاميرا
        if hasattr(self, 'air_thread') and self.air_thread.isRunning():
            self.air_thread.stop()
            self.air_thread.wait()

        # 2. شغل النيو (استخدم try عشان لو كود النيو فيه غلطة البرنامج الأساسي ميفصلش)
        try:
            self.p_new = Process(target=New_panda)
            self.p_new.daemon = True
            self.p_new.start()
            
            # 3. المراقبة
            try: self.monitor_timer.timeout.disconnect()
            except: pass
            self.monitor_timer.timeout.connect(self.check_new_design_status)
            self.monitor_timer.start(1000)
        except Exception as e:
            print(f"❌ Failed to start New Design: {e}")
            self.restart_main_gestures()

    def check_new_design_status(self):
        if self.p_new and not self.p_new.is_alive():
            print("🔙 Returning from New Design...")
            self.monitor_timer.stop()
            self.restart_main_gestures()

    def resizeEvent(self, event):
        center = self.rect().center()
        self.main_btn.move(center.x() - 87, center.y() - 87)
        if hasattr(self, 'pulse_anim'): 
            self.pulse_anim.stop(); self.setup_pulse()
        super().resizeEvent(event)

    def toggle_menu(self):
        if not self.menu_open:
            self.update_positions(animate=True); self.menu_open = True
        else:
            for b in self.btns_list: b.hide()
            self.menu_open = False

    def update_positions(self, animate=False):
        center = self.rect().center(); ox, oy = 300, 220
        pos = [(center.x()-ox-87, center.y()-oy-87), (center.x()-ox-87, center.y()+oy-87),
               (center.x()+ox-87, center.y()-oy-87), (center.x()+ox-87, center.y()+oy-87)]
        self.anims = [] 
        for i, btn in enumerate(self.btns_list):
            target = QPoint(int(pos[i][0]), int(pos[i][1])); btn.show()
            if animate:
                a = QPropertyAnimation(btn, b"pos"); a.setDuration(600); a.setStartValue(self.main_btn.pos())
                a.setEndValue(target); a.setEasingCurve(QEasingCurve.OutBack); self.anims.append(a); a.start()
            else: btn.move(target)

    def run_logic(self, file_name):
        """لتشغيل ملفات الـ logic الأخرى مثل New Design"""
        if os.path.exists(file_name):
            # يفضل استخدام Process برضه لو الملفات دي فيها كاميرا أو AI
            os.system(f"python {file_name}")

    def update_space(self):
        for i in range(len(self.meteors)):#بحدد الشهب قد اي
            self.meteors[i][0] -= self.meteors[i][2]; self.meteors[i][1] += self.meteors[i][2] * 0.5 #دي كدا بعد ما حددت انا في الاصل هما اربعه بس بيتكرروا
            if self.meteors[i][0] < -200: self.meteors[i] = [2500, random.randint(0, 600), random.randint(10, 25)]#حركات الشهاب راسي وافقي
        self.update()#عشان يكرر

    def paintEvent(self, event):
        painter = QPainter(self)#دي كدا فرشة الرسم بتاعتي
        if not self.bg_image.isNull(): painter.drawImage(self.rect(), self.bg_image)#دي كدا عشان انا حاطط خلفيه فهنا بيتاكد هي موجوده ام لا وبيرسمها علي حجم الشاشه
        for s in self.stars:#عمل النجوم
            painter.setPen(QPen(QColor(255, 255, 255, random.randint(150, 255)), 2))#مهمه لي بتعملي لون النجمه دي اول جزء والتاني شكلها اي ابيض
            painter.drawPoint(int(s[0]), int(s[1]))# وكمان عشان تنتشر ازاي رسم النجمه كبيره صغيره وهكذا
        for m in self.meteors:#كدا بقا برسم الشهاب 
            grad = QLinearGradient(m[0], m[1], m[0]+120, m[1]-60); grad.setColorAt(0, QColor(0, 255, 255, 200)); grad.setColorAt(1, Qt.transparent)#مهمه لتدرج اللون الجزء1 ورسم اللون
            painter.setPen(QPen(grad, 3)); painter.drawLine(int(m[0]), int(m[1]), int(m[0]+100), int(m[1]-50))#خاصه بالشهب وتتحرك ازاي وفين والحجم وكدا
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.close()#تفعيل زر ال Esc عشان اعرف اخرج من البرنامج
    
    def closeEvent(self, event):
        self.air_thread.stop()
        self.air_thread.wait()
        event.accept()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support() 
    
    # 2. إعدادات جودة الشاشة والدقة
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # 3. تشغيل تطبيق PyQt
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps) # جودة رسومات عالية
    
    # 4. إنشاء وتشغيل الواجهة الرئيسية
    window = MainWindow()
    
    sys.exit(app.exec_())