import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QPushButton
from PyQt5.QtCore import Qt, QTimer
from direct.showbase.ShowBase import ShowBase
from panda3d.core import LineSegs, WindowProperties

class Neurix3DEngine(ShowBase):
    def __init__(self, host_widget):
        # تشغيل بدون نافذة مستقلة
        ShowBase.__init__(self, windowType='none')
        
        props = WindowProperties()
        props.setParentWindow(int(host_widget.winId()))
        props.setOrigin(0, 0)
        props.setSize(host_widget.width(), host_widget.height())
        
        # تعطيل الخصائص اللي بتعمل صراع مع ويندوز
        props.set_focus(False)
        props.set_cursor_hidden(False)
        
        self.makeDefaultPipe()
        self.openDefaultWindow(props=props)
        self.set_background_color(0.3, 0.3, 0.3, 1) # الخلفية الرمادية
        self.model_node = None

    def create_extruded_shape(self, points, depth, color_vec):
        if self.model_node: self.model_node.removeNode()
        if len(points) < 2: return
            
        segs = LineSegs()
        segs.setThickness(4.0)
        segs.setColor(color_vec)

        for z in [0, -depth]:
            segs.moveTo(points[0][0], points[0][1], z)
            for x, y in points[1:]:
                segs.drawTo(x, y, z)
            segs.drawTo(points[0][0], points[0][1], z)

        for x, y in points:
            segs.moveTo(x, y, 0)
            segs.drawTo(x, y, -depth)

        self.model_node = self.render.attachNewNode(segs.create())
        self.model_node.setPos(0, 40, 0)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NEURIX - Stable Build")
        self.setFixedSize(1100, 850)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.points_raw = []
        self.current_color = (1, 1, 1, 1) 

        self.init_ui()
        self.show()
        # تأخير 200ms يضمن إن ويندوز خصص الـ ID للنافذة صح
        QTimer.singleShot(200, self.init_engine)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # لوحة الألوان
        self.color_bar = QHBoxLayout()
        colors = {'White':(1,1,1,1), 'Red':(1,0,0,1), 'Yellow':(1,1,0,1), 'Green':(0,1,0,1), 'Blue':(0,0,1,1)}
        for c_name, c_vec in colors.items():
            btn = QPushButton(c_name)
            btn.setStyleSheet(f"background-color: {c_name.lower()}; color: black; font-weight: bold;")
            btn.clicked.connect(lambda ch, v=c_vec: self.set_color(v))
            self.color_bar.addWidget(btn)
        self.layout.addLayout(self.color_bar)

        # حاوية الرسم (Panda3D)
        self.container = QWidget()
        self.container.setMinimumSize(800, 500)
        # أهم الـ Flags لمنع رسائل التحذير:
        self.container.setAttribute(Qt.WA_NativeWindow)
        self.container.setAttribute(Qt.WA_PaintOnScreen)
        self.container.setAttribute(Qt.WA_NoSystemBackground)
        self.container.setAttribute(Qt.WA_OpaquePaintEvent)
        self.layout.addWidget(self.container)

        self.depth_slider = QSlider(Qt.Horizontal)
        self.depth_slider.setRange(0, 200)
        self.depth_slider.valueChanged.connect(self.refresh_3d)
        self.layout.addWidget(self.depth_slider)

    def set_color(self, v):
        self.current_color = v
        self.refresh_3d()

    def mouseMoveEvent(self, event):
        if self.container.underMouse():
            pos = self.container.mapFromGlobal(event.globalPos())
            x = (pos.x() - (self.container.width()/2)) / 30
            y = -(pos.y() - (self.container.height()/2)) / 30
            self.points_raw.append((x, y))
            self.refresh_3d()

    def init_engine(self):
        try:
            self.engine = Neurix3DEngine(self.container)
        except Exception as e:
            print(f"Engine Startup Error: {e}")

    def refresh_3d(self):
        if hasattr(self, 'engine') and self.points_raw:
            d = self.depth_slider.value() / 10.0
            self.engine.create_extruded_shape(self.points_raw, d, self.current_color)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())