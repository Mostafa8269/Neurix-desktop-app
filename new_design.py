from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, LineSegs, WindowProperties, ClockObject, AntialiasAttrib, Vec3, TextNode
from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenText

globalClock = ClockObject.getGlobalClock()

class ModularDesignApp(ShowBase):
    def __init__(self):
        super().__init__()

        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setBackgroundColor(0.15, 0.15, 0.18)
        self.disableMouse()
        
        self.camera.setPos(70, -140, 60)
        self.camera.lookAt(0, 0, 0)
        self.mouse_sensitivity = 0.2
        self.speed = 40
        
        self.current_part = None
        self.assembled_parts = []
        self.preview_models = [] 

        self.setup_lights()
        self.create_grid(200)
        self.create_center_point()
        
        self.sub_menus = {}
        self.create_responsive_top_library()
        self.create_advanced_sidebar()

        self.accept("enter", self.finalize_part)
        self.accept("escape", exit)
        self.accept("delete", self.delete_current_part)
        self.accept("backspace", self.delete_current_part)
        
        self.camera_rot_active = False
        self.accept("mouse3", self.set_camera_rot, [True])  
        self.accept("mouse3-up", self.set_camera_rot, [False])

        self.taskMgr.add(self.update_task, "update_task")

    def create_center_point(self):
        self.center_dot = OnscreenText(text='+', pos=(0, 0), scale=0.08, fg=(1, 1, 1, 0.7), align=TextNode.ACenter)

    def create_grid(self, size):
        lines = LineSegs()
        for i in range(-size, size + 1, 5):
            lines.setThickness(1.0)
            lines.setColor(0.3, 0.3, 0.3, 0.2)
            lines.moveTo(i, -size, 0); lines.drawTo(i, size, 0)
            lines.moveTo(-size, i, 0); lines.drawTo(size, i, 0)
        grid_node = self.render.attachNewNode(lines.create())
        grid_node.setTransparency(1)

    def create_responsive_top_library(self):
        """مكتبة الأشكال - تم تصغير الأزرار العلوية"""
        self.top_panel = DirectFrame(frameColor=(0, 0, 0, 0.8), 
                                     frameSize=(-2.3, 2.3, -0.12, 0.12),
                                     parent=self.a2dTopCenter, pos=(0, 0, -0.12),
                                     scale=0.6) # تصغير حجم اللوحة بالكامل
        
        shape_items = [
            ("Moraaba", "models/box", (1,0,0,1)),
            ("Mostateel", "models/box", (0,1,0,1)),
            ("Dayra", "models/misc/sphere", (0,0,1,1)),
            ("Mothalath", "models/box", (1,1,0,1)),
            ("Kora", "models/misc/sphere", (1,0,1,1)),
            ("Ostowana", "models/box", (0,1,1,1)),
            ("Makhrut", "models/misc/sphere", (1,0.5,0,1)),
            ("Haram", "models/box", (0.5,0.5,0.5,1)),
            ("Najma", "models/box", (1,1,1,1)),
            ("Khat", "models/box", (1,1,1,1)),
            ("Sahm", "models/box", (0,1,0,1)),
            ("Hexa", "models/box", (0.3,0.3,0.3,1)),
            ("Oval", "models/misc/sphere", (0.8,0.4,0.2,1)),
            ("Curve", "models/box", (0.4,0.4,1,1)),
            ("Brush", "models/box", (1,0.8,0.8,1)),
            ("Grid2D", "models/box", (1,1,1,0.5)),
            ("GridSq", "models/box", (1,1,1,0.3)),
            ("Nakes", "models/misc/sphere", (0.5,0,0,1))
        ]

        x_start = -2.1
        for i, (p_name, m_path, p_color) in enumerate(shape_items):
            container = self.top_panel.attachNewNode(f"cont_{p_name}")
            container.setPos(x_start + (i * 0.25), 0, 0)
            try:
                model = self.loader.loadModel(m_path)
                model.reparentTo(container)
                model.setScale(0.015)
                model.setColor(p_color)
                self.preview_models.append(model)
                OnscreenText(text=p_name, pos=(0, -0.09), scale=0.04, fg=(1,1,1,1), parent=container)
            except: pass

            DirectButton(parent=container, frameColor=(0,0,0,0), 
                         frameSize=(-0.1, 0.1, -0.1, 0.1),
                         command=self.add_shape, extraArgs=[p_name, m_path, p_color])

    def create_advanced_sidebar(self):
        """السايد بار - تم تصغير الأزرار الجانبية"""
        self.side_bar = DirectFrame(frameColor=(0.1, 0.1, 0.1, 0.9),
                                    frameSize=(-0.12, 0.12, -0.95, 0.95),
                                    parent=self.a2dLeftCenter, pos=(0.12, 0, 0))

        menu_data = [
            ("Add", ["Fix Part", "Clear All"]),
            ("Select", ["Delete Part"]),
            ("Move", ["Up (Z+)", "Down (Z-)", "Right (X+)", "Left (X-)"]),
            ("Rotate", ["Rot H+", "Rot P+", "Rot R+"]),
            ("Zoom", ["In (+)", "Out (-)"])
        ]

        # ضبط المسافات لتكون الأزرار أصغر وأكثر ترتيباً
        y_positions = {"Add": 0.85, "Select": 0.65, "Move": 0.45, "Rotate": 0.05, "Zoom": -0.25}

        for main_btn, sub_options in menu_data:
            curr_y = y_positions[main_btn]
            # زر رئيسي أصغر
            DirectButton(text=main_btn, scale=0.04, pos=(0, 0, curr_y), parent=self.side_bar, 
                         frameColor=(0.3, 0.3, 0.3, 1), text_fg=(1, 1, 1, 1), 
                         frameSize=(-2.2, 2.2, -0.6, 0.6), command=self.toggle_menu, extraArgs=[main_btn])
            
            sub_frame = DirectFrame(parent=self.side_bar, frameColor=(0,0,0,0), pos=(0, 0, curr_y - 0.1))
            self.sub_menus[main_btn] = sub_frame
            sub_y = 0
            for opt in sub_options:
                # زر فرعي أصغر
                DirectButton(text=opt, scale=0.03, pos=(0.06, 0, sub_y), parent=sub_frame, 
                             frameColor=(0.2, 0.4, 0.6, 1), text_fg=(1, 1, 1, 1), 
                             frameSize=(-3.0, 3.0, -0.5, 0.5), command=self.handle_action, extraArgs=[opt])
                sub_y -= 0.07
            sub_frame.hide()

    def add_shape(self, name, path, color):
        if self.current_part: self.finalize_part()
        self.current_part = self.loader.loadModel(path)
        self.current_part.reparentTo(self.render)
        self.current_part.setPos(0, 0, 5)
        self.current_part.setColor(color)

        if name == "Moraaba": self.current_part.setScale(4, 4, 4)
        elif name == "Mostateel": self.current_part.setScale(8, 2, 4)
        elif name == "Dayra": self.current_part.setScale(5, 5, 0.1)
        elif name == "Ostowana": self.current_part.setScale(1.5, 1.5, 8)
        elif name == "Khat": self.current_part.setScale(15, 0.1, 0.1)
        elif name == "Mothalath": 
            self.current_part.setScale(5, 0.1, 5)
            self.current_part.setShear((0, 25, 0))
        else: self.current_part.setScale(3)

    def toggle_menu(self, menu_name):
        for name, frame in self.sub_menus.items():
            if name == menu_name:
                if frame.isHidden(): frame.show()
                else: frame.hide()
            else: frame.hide()

    def handle_action(self, action):
        if not self.current_part and action not in ["Clear All"]: return
        if action == "In (+)": self.current_part.setScale(self.current_part.getScale() * 1.1)
        elif action == "Out (-)": self.current_part.setScale(self.current_part.getScale() * 0.9)
        elif action == "Up (Z+)": self.current_part.setZ(self.current_part.getZ() + 2)
        elif action == "Down (Z-)": self.current_part.setZ(self.current_part.getZ() - 2)
        elif action == "Right (X+)": self.current_part.setX(self.current_part.getX() + 2)
        elif action == "Left (X-)": self.current_part.setX(self.current_part.getX() - 2)
        elif action == "Rot H+": self.current_part.setH(self.current_part.getH() + 22.5)
        elif action == "Delete Part": self.delete_current_part()
        elif action == "Fix Part": self.finalize_part()
        elif action == "Clear All":
            for part in self.assembled_parts: part.removeNode()
            self.assembled_parts = []; self.delete_current_part()

    def update_task(self, task):
        dt = globalClock.getDt()
        for model in self.preview_models: model.setH(model.getH() + 80 * dt)
        if self.camera_rot_active and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0); x, y = md.getX(), md.getY()
            center_x, center_y = self.win.getXSize() // 2, self.win.getYSize() // 2
            self.camera.setH(self.camera.getH() - (x - center_x) * self.mouse_sensitivity)
            self.camera.setP(self.camera.getP() - (y - center_y) * self.mouse_sensitivity)
            self.win.movePointer(0, center_x, center_y)
        return task.cont

    def setup_lights(self):
        self.render.setLight(self.render.attachNewNode(AmbientLight("al")))
        dl = DirectionalLight("dl"); dlnp = self.render.attachNewNode(dl)
        dlnp.setHpr(45, -45, 0); self.render.setLight(dlnp)

    def set_camera_rot(self, active):
        self.camera_rot_active = active
        props = WindowProperties(); props.setCursorHidden(active); self.win.requestProperties(props)

    def delete_current_part(self, arg=None):
        if self.current_part: self.current_part.removeNode(); self.current_part = None

    def finalize_part(self, arg=None):
        if self.current_part:
            self.current_part.setColor(self.current_part.getColor() * 0.9)
            self.assembled_parts.append(self.current_part)
            self.current_part = None

app = ModularDesignApp()
app.run()