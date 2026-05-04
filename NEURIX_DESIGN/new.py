from direct.showbase.ShowBase import ShowBase
from panda3d.core import (AmbientLight, DirectionalLight, LineSegs, WindowProperties,
                           ClockObject, AntialiasAttrib, Vec3, TextNode, ModelPool,
                           loadPrcFileData, GeomVertexFormat, GeomVertexData,
                           GeomVertexWriter, Geom, GeomTriangles, GeomNode,
                           GeomLines, NodePath)
from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenText
import math

loadPrcFileData("", "load-file-type panda3d-gltf")

globalClock = ClockObject.getGlobalClock()

# ─────────────────────────────────────────────
#  دوال بناء الأشكال الهندسية يدويًا
# ─────────────────────────────────────────────

def make_cube():
    """مكعب متساوي الأضلاع"""
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("cube", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")

    faces = [
        # (verts x4,  normal)
        ([(-.5,-.5,-.5),(-.5,.5,-.5),(.5,.5,-.5),(.5,-.5,-.5)], (0,0,-1)),
        ([(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],      (0,0, 1)),
        ([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5)],  (0,-1,0)),
        ([(-.5,.5,-.5),(-.5,.5,.5),(.5,.5,.5),(.5,.5,-.5)],       (0, 1,0)),
        ([(-.5,-.5,-.5),(-.5,-.5,.5),(-.5,.5,.5),(-.5,.5,-.5)],  (-1,0,0)),
        ([(.5,-.5,-.5),(.5,.5,-.5),(.5,.5,.5),(.5,-.5,.5)],       (1, 0,0)),
    ]
    tris = GeomTriangles(Geom.UHStatic)
    vi = 0
    for verts, norm in faces:
        for v in verts:
            vw.addData3(*v); nw.addData3(*norm)
        tris.addVertices(vi, vi+1, vi+2)
        tris.addVertices(vi, vi+2, vi+3)
        vi += 4

    geom = Geom(vdata); geom.addPrimitive(tris)
    node = GeomNode("cube"); node.addGeom(geom)
    return NodePath(node)


def make_flat_box():
    """مربع (صندوق مسطّح – الارتفاع نصف العرض)"""
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("flat_box", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")

    # نفس وجوه المكعب لكن بأبعاد مختلفة (1 × 1 × 0.5)
    hx, hy, hz = .5, .5, .25
    faces = [
        ([(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz),(hx,-hy,-hz)], (0,0,-1)),
        ([(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)],      (0,0, 1)),
        ([(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)],  (0,-1,0)),
        ([(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)],       (0, 1,0)),
        ([(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)],  (-1,0,0)),
        ([(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz),(hx,-hy,hz)],       (1, 0,0)),
    ]
    tris = GeomTriangles(Geom.UHStatic)
    vi = 0
    for verts, norm in faces:
        for v in verts: vw.addData3(*v); nw.addData3(*norm)
        tris.addVertices(vi, vi+1, vi+2)
        tris.addVertices(vi, vi+2, vi+3)
        vi += 4

    geom = Geom(vdata); geom.addPrimitive(tris)
    node = GeomNode("flat_box"); node.addGeom(geom)
    return NodePath(node)


def make_cuboid():
    """متوازي مستطيلات (2 × 1 × 0.5)"""
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("cuboid", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")

    hx, hy, hz = 1.0, .5, .25
    faces = [
        ([(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz),(hx,-hy,-hz)], (0,0,-1)),
        ([(-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)],      (0,0, 1)),
        ([(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy,hz),(-hx,-hy,hz)],  (0,-1,0)),
        ([(-hx,hy,-hz),(-hx,hy,hz),(hx,hy,hz),(hx,hy,-hz)],       (0, 1,0)),
        ([(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)],  (-1,0,0)),
        ([(hx,-hy,-hz),(hx,hy,-hz),(hx,hy,hz),(hx,-hy,hz)],       (1, 0,0)),
    ]
    tris = GeomTriangles(Geom.UHStatic)
    vi = 0
    for verts, norm in faces:
        for v in verts: vw.addData3(*v); nw.addData3(*norm)
        tris.addVertices(vi, vi+1, vi+2)
        tris.addVertices(vi, vi+2, vi+3)
        vi += 4

    geom = Geom(vdata); geom.addPrimitive(tris)
    node = GeomNode("cuboid"); node.addGeom(geom)
    return NodePath(node)


def make_sphere(segs=24):
    """كرة مُولَّدة إجرائيًا"""
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("sphere", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")

    rings = segs // 2
    for r in range(rings + 1):
        phi = math.pi * r / rings
        for s in range(segs + 1):
            theta = 2 * math.pi * s / segs
            x = math.sin(phi) * math.cos(theta)
            y = math.sin(phi) * math.sin(theta)
            z = math.cos(phi)
            vw.addData3(x * .5, y * .5, z * .5)
            nw.addData3(x, y, z)

    tris = GeomTriangles(Geom.UHStatic)
    for r in range(rings):
        for s in range(segs):
            a = r * (segs + 1) + s
            b = a + segs + 1
            tris.addVertices(a, b, a + 1)
            tris.addVertices(a + 1, b, b + 1)

    geom = Geom(vdata); geom.addPrimitive(tris)
    node = GeomNode("sphere"); node.addGeom(geom)
    return NodePath(node)


def make_cylinder(segs=24):
    """أسطوانة مضلّعة"""
    fmt = GeomVertexFormat.getV3n3()
    vdata = GeomVertexData("cylinder", fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")

    r, h = .5, 1.0
    # جدار جانبي
    for i in range(segs + 1):
        a = 2 * math.pi * i / segs
        cx, cy = math.cos(a), math.sin(a)
        for z in (0, h):
            vw.addData3(r * cx, r * cy, z - h / 2)
            nw.addData3(cx, cy, 0)

    tris = GeomTriangles(Geom.UHStatic)
    side_verts = (segs + 1) * 2
    for i in range(segs):
        base = i * 2
        tris.addVertices(base, base + 2, base + 1)
        tris.addVertices(base + 1, base + 2, base + 3)

    # قاعدة أسفل
    bot_center = side_verts
    vw.addData3(0, 0, -h / 2); nw.addData3(0, 0, -1)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        vw.addData3(r * math.cos(a), r * math.sin(a), -h / 2)
        nw.addData3(0, 0, -1)
    for i in range(segs):
        tris.addVertices(bot_center, bot_center + 1 + (i + 1) % segs, bot_center + 1 + i)

    # قاعدة أعلى
    top_center = bot_center + segs + 1
    vw.addData3(0, 0, h / 2); nw.addData3(0, 0, 1)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        vw.addData3(r * math.cos(a), r * math.sin(a), h / 2)
        nw.addData3(0, 0, 1)
    for i in range(segs):
        tris.addVertices(top_center, top_center + 1 + i, top_center + 1 + (i + 1) % segs)

    geom = Geom(vdata); geom.addPrimitive(tris)
    node = GeomNode("cylinder"); node.addGeom(geom)
    return NodePath(node)


# خريطة الأشكال: اسم → دالة إنشاء، مقياس عرض، مقياس مشهد
SHAPE_BUILDERS = {
    "Cube":     (make_cube,     0.06, 6),
    "Square":   (make_flat_box, 0.06, 6),
    "Cuboid":   (make_cuboid,   0.06, 8),
    "Sphere":   (make_sphere,   0.06, 6),
    "Cylinder": (make_cylinder, 0.05, 6),
}

# ─────────────────────────────────────────────
#  التطبيق الرئيسي
# ─────────────────────────────────────────────

class ModularDesignApp(ShowBase):
    def __init__(self):
        super().__init__()

        ModelPool.releaseAllModels()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setBackgroundColor(0.15, 0.15, 0.18)
        self.disableMouse()

        self.camera.setPos(70, -140, 60)
        self.camera.lookAt(0, 0, 0)
        self.mouse_sensitivity = 0.2

        self.current_part = None
        self.assembled_parts = []
        self.preview_models = []

        self.setup_lights()
        self.create_grid(200)
        self.create_center_point()

        self.main_menu_buttons = {}
        self.sub_menus = {}

        self.create_top_libraries()
        self.create_advanced_sidebar()
        self.create_modern_color_sidebar()

        self.accept("enter", self.finalize_part)
        self.accept("escape", exit)
        self.accept("delete", self.delete_current_part)

        self.camera_rot_active = False
        self.accept("mouse3",    self.set_camera_rot, [True])
        self.accept("mouse3-up", self.set_camera_rot, [False])

        self.taskMgr.add(self.update_task, "update_task")

    # ── واجهة ──────────────────────────────────

    def create_center_point(self):
        self.center_dot = OnscreenText(text='+', pos=(0, 0), scale=0.08,
                                       fg=(1, 1, 1, 0.7), align=TextNode.ACenter)

    def create_grid(self, size):
        lines = LineSegs()
        for i in range(-size, size + 1, 5):
            lines.setThickness(1.0)
            lines.setColor(0.3, 0.3, 0.3, 0.2)
            lines.moveTo(i, -size, 0); lines.drawTo(i, size, 0)
            lines.moveTo(-size, i, 0); lines.drawTo(size, i, 0)
        grid_node = self.render.attachNewNode(lines.create())
        grid_node.setTransparency(1)

    # ── مكتبة الحيوانات + الأشكال (علوية) ──────

    def create_top_libraries(self):
        self.top_panel = DirectFrame(frameColor=(0, 0, 0, 0.8),
                                     frameSize=(-1.3, 1.3, -0.12, 0.12),
                                     parent=self.a2dTopCenter, pos=(0, 0, -0.15),
                                     scale=0.8)
        self.top_panel.hide()

        self.animal_items = [
            ("Lion",   "Lion.glb",                          (0.8, 0.8, 0.8, 1)),
            ("Rabbit", "White_Rabbit.glb",                  (0.8, 0.8, 0.8, 1)),
            ("Horse",  "Basic_Chunky_Horse_Square.glb",     (0.8, 0.8, 0.8, 1)),
            ("B-fly",  "butterfly.glb",                     (0.9, 0.5, 0.9, 1)),
            ("Tiger",  "smilodon_or_sabre_tooth_tiger.glb", (1, 0.5, 0, 1)),
        ]

        # أشكال الـ shapes الجديدة (اسم فقط – بدون مسار ملف)
        self.shape_items = list(SHAPE_BUILDERS.keys())   # ["Cube","Square","Cuboid","Sphere","Cylinder"]

        self.animals_node = self.top_panel.attachNewNode("animals_node")
        self.shapes_node  = self.top_panel.attachNewNode("shapes_node")

        self.build_animal_items(self.animal_items, self.animals_node)
        self.build_shape_items(self.shape_items,   self.shapes_node)

    def build_animal_items(self, items, parent_node):
        x_start = -0.8
        spacing = 0.45
        for i, (p_name, m_path, p_color) in enumerate(items):
            container = parent_node.attachNewNode(f"cont_{p_name}")
            container.setPos(x_start + (i * spacing), 0, 0)
            try:
                model = self.loader.loadModel(m_path, noCache=True)
                model.reparentTo(container)
                path_l = m_path.lower()
                if   "butterfly" in path_l: model.setScale(0.015); model.setZ(-0.02)
                elif "horse"     in path_l: model.setScale(0.02);  model.setZ(-0.03)
                elif "rabbit"    in path_l: model.setScale(0.007); model.setZ(-0.02)
                elif "tiger"     in path_l: model.setScale(0.008); model.setZ(-0.04)
                elif "lion"      in path_l: model.setScale(0.005); model.setZ(-0.03)
                else:                       model.setScale(0.008)
                model.setColor(p_color)
                self.preview_models.append(model)
                OnscreenText(text=p_name, pos=(0, -0.09), scale=0.035,
                             fg=(1,1,1,1), parent=container)
                DirectButton(parent=container, frameColor=(0,0,0,0),
                             frameSize=(-0.15, 0.15, -0.1, 0.1),
                             command=self.add_animal,
                             extraArgs=[p_name, m_path, p_color])
            except:
                pass

    def build_shape_items(self, shape_names, parent_node):
        """بناء معاينة الأشكال الهندسية إجرائيًا"""
        x_start  = -0.9
        spacing  = 0.45
        colors   = [(0.6,0.8,1,1),(1,0.8,0.4,1),(0.8,0.5,1,1),(0.4,1,0.7,1),(1,0.5,0.5,1)]
        for i, name in enumerate(shape_names):
            container = parent_node.attachNewNode(f"cont_{name}")
            container.setPos(x_start + (i * spacing), 0, 0)

            builder_fn, preview_scale, _ = SHAPE_BUILDERS[name]
            model = builder_fn()
            model.reparentTo(container)
            model.setScale(preview_scale)
            model.setColor(colors[i % len(colors)])
            self.preview_models.append(model)

            OnscreenText(text=name, pos=(0, -0.09), scale=0.035,
                         fg=(1,1,1,1), parent=container)
            DirectButton(parent=container, frameColor=(0,0,0,0),
                         frameSize=(-0.15, 0.15, -0.1, 0.1),
                         command=self.add_procedural_shape,
                         extraArgs=[name])

    # ── إضافة نماذج ──────────────────────────

    def add_animal(self, name, path, color):
        if self.current_part: self.finalize_part()
        try:
            self.current_part = self.loader.loadModel(path, noCache=True)
            self.current_part.reparentTo(self.render)
            self.current_part.setPos(0, 0, 5)
            self.current_part.setColor(1, 1, 1, 1)
            path_l = path.lower()
            if   "butterfly" in path_l: self.current_part.setScale(0.6)
            elif "tiger"     in path_l: self.current_part.setScale(1.5)
            elif "lion"      in path_l: self.current_part.setScale(0.15)
            elif "rabbit"    in path_l: self.current_part.setScale(4.0)
            elif "horse"     in path_l: self.current_part.setScale(7.0)
            else:                       self.current_part.setScale(1)
        except:
            pass

    def add_procedural_shape(self, name):
        if self.current_part: self.finalize_part()
        builder_fn, _, scene_scale = SHAPE_BUILDERS[name]
        self.current_part = builder_fn()
        self.current_part.reparentTo(self.render)
        self.current_part.setPos(0, 0, 5)
        self.current_part.setScale(scene_scale)
        self.current_part.setColor(1, 1, 1, 1)

    # ── تبويب المكتبات ──────────────────────

    def toggle_library_tab(self, tab_type):
        if tab_type == "animals":
            if self.top_panel.isHidden() or self.animals_node.isHidden():
                self.top_panel.show(); self.animals_node.show(); self.shapes_node.hide()
            else:
                self.top_panel.hide()
        elif tab_type == "shapes":
            if self.top_panel.isHidden() or self.shapes_node.isHidden():
                self.top_panel.show(); self.shapes_node.show(); self.animals_node.hide()
            else:
                self.top_panel.hide()

    # ── الشريط الجانبي للألوان ───────────────

    def create_modern_color_sidebar(self):
        self.color_sidebar = DirectFrame(frameColor=(0.05, 0.05, 0.05, 0.85),
                                         frameSize=(-0.1, 0.1, -1.2, 1.2),
                                         parent=self.a2dRightCenter, pos=(-0.1, 0, 0))
        OnscreenText(text="Colors", pos=(0, 0.95), scale=0.05,
                     fg=(1,1,1,1), parent=self.color_sidebar, align=TextNode.ACenter)
        colors = [
            (0.9,0.1,0.1,1),(0.1,0.9,0.1,1),(0.1,0.3,0.9,1),
            (0.9,0.9,0.1,1),(1,0.5,0,1),(1,0,1,1),
            (0,1,1,1),(0.5,0,0.5,1),(0,0,0.5,1),
            (1,1,1,1),(0.5,0.5,0.5,1),(0.2,0.2,0.2,1),
            (1,0.8,0.6,1),(0.6,0.3,0.1,1),(0.3,0.8,0.5,1),
            (0.9,0.6,0.8,1),(0.7,0.9,0.3,1),(0.4,0.2,0.6,1),
        ]
        y_pos = 0.85
        for clr in colors:
            DirectButton(parent=self.color_sidebar, frameColor=clr,
                         frameSize=(-0.045,0.045,-0.045,0.045), pos=(0,0,y_pos),
                         command=self.change_color, extraArgs=[clr])
            y_pos -= 0.10
        self.color_sidebar.hide()

    def toggle_color_sidebar(self):
        if self.color_sidebar.isHidden(): self.color_sidebar.show()
        else:                             self.color_sidebar.hide()

    def change_color(self, color):
        if self.current_part:
            self.current_part.setMaterialOff(1)
            self.current_part.setTextureOff(1)
            self.current_part.setColor(color, 1)

    # ── الشريط الجانبي الأيسر ────────────────

    def create_advanced_sidebar(self):
        self.side_bar = DirectFrame(frameColor=(0.1,0.1,0.1,0.9),
                                    frameSize=(-0.18,0.18,-1,1),
                                    parent=self.a2dLeftCenter, pos=(0.18,0,0))
        self.menu_data = [
            ("Models",  ["Toggle Animals"]),
            ("Shapes",  ["Toggle Shapes"]),
            ("Colors",  ["Toggle Colors"]),
            ("Add",     ["Fix Part", "Clear All"]),
            ("Move",    ["Up (Z+)", "Down (Z-)", "Right (X+)", "Left (X-)"]),
            ("Zoom",    ["In (+)", "Out (-)"]),
            ("Rotate",  ["Rot H+", "Rot H-", "Rot P+", "Rot P-", "Rot R+", "Rot R-"]),
            ("Select",  ["Delete Part"]),
        ]
        for name, options in self.menu_data:
            btn = DirectButton(text=name, scale=0.05, parent=self.side_bar,
                               frameColor=(0.25,0.25,0.25,1), text_fg=(1,1,1,1),
                               command=self.toggle_menu, extraArgs=[name])
            self.main_menu_buttons[name] = btn
            sub_frame = DirectFrame(parent=self.side_bar, frameColor=(0,0,0,0))
            self.sub_menus[name] = sub_frame
            sy = -0.08
            for opt in options:
                if opt == "Toggle Animals":
                    cmd, args = lambda: self.toggle_library_tab("animals"), []
                elif opt == "Toggle Shapes":
                    cmd, args = lambda: self.toggle_library_tab("shapes"), []
                elif opt == "Toggle Colors":
                    cmd, args = self.toggle_color_sidebar, []
                else:
                    cmd, args = self.handle_action, [opt]
                DirectButton(text=opt, scale=0.035, pos=(0,0,sy),
                             parent=sub_frame, frameColor=(0.2,0.4,0.6,1),
                             text_fg=(1,1,1,1), frameSize=(-3.5,3.5,-0.6,0.8),
                             command=cmd, extraArgs=args)
                sy -= 0.11
            sub_frame.hide()
        self.reposition_menus()

    def reposition_menus(self):
        current_y = 0.9
        for name, options in self.menu_data:
            self.main_menu_buttons[name].setPos(0, 0, current_y)
            self.sub_menus[name].setPos(0, 0, current_y)
            if not self.sub_menus[name].isHidden():
                current_y -= (len(options) * 0.11) + 0.15
            else:
                current_y -= 0.15

    def toggle_menu(self, menu_name):
        for name, frame in self.sub_menus.items():
            if name == menu_name: frame.show() if frame.isHidden() else frame.hide()
            else: frame.hide()
        self.reposition_menus()

    def handle_action(self, action):
        if action == "Clear All":
            for p in self.assembled_parts: p.removeNode()
            self.assembled_parts = []
            if self.current_part: self.current_part.removeNode(); self.current_part = None
            return
        if not self.current_part: return
        if   action == "In (+)":    self.current_part.setScale(self.current_part.getScale() * 1.1)
        elif action == "Out (-)":   self.current_part.setScale(self.current_part.getScale() * 0.9)
        elif action == "Up (Z+)":   self.current_part.setZ(self.current_part.getZ() + 2)
        elif action == "Down (Z-)": self.current_part.setZ(self.current_part.getZ() - 2)
        elif action == "Right (X+)":self.current_part.setX(self.current_part.getX() + 2)
        elif action == "Left (X-)": self.current_part.setX(self.current_part.getX() - 2)
        elif action == "Rot H+":    self.current_part.setH(self.current_part.getH() + 22.5)
        elif action == "Rot H-":    self.current_part.setH(self.current_part.getH() - 22.5)
        elif action == "Rot P+":    self.current_part.setP(self.current_part.getP() + 22.5)
        elif action == "Rot P-":    self.current_part.setP(self.current_part.getP() - 22.5)
        elif action == "Rot R+":    self.current_part.setR(self.current_part.getR() + 22.5)
        elif action == "Rot R-":    self.current_part.setR(self.current_part.getR() - 22.5)
        elif action == "Fix Part":  self.finalize_part()
        elif action == "Delete Part": self.delete_current_part()

    # ── حلقة التحديث ────────────────────────

    def update_task(self, task):
        dt = globalClock.getDt()
        for m in self.preview_models: m.setH(m.getH() + 80 * dt)
        if self.camera_rot_active and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            x, y = md.getX(), md.getY()
            cx, cy = self.win.getXSize() // 2, self.win.getYSize() // 2
            self.camera.setH(self.camera.getH() - (x - cx) * self.mouse_sensitivity)
            self.camera.setP(self.camera.getP() - (y - cy) * self.mouse_sensitivity)
            self.win.movePointer(0, cx, cy)
        return task.cont

    # ── مساعدات ─────────────────────────────

    def setup_lights(self):
        self.render.setLight(self.render.attachNewNode(AmbientLight("al")))
        dl = DirectionalLight("dl"); dlnp = self.render.attachNewNode(dl)
        dlnp.setHpr(45, -45, 0); self.render.setLight(dlnp)

    def set_camera_rot(self, active):
        self.camera_rot_active = active
        props = WindowProperties(); props.setCursorHidden(active)
        self.win.requestProperties(props)

    def delete_current_part(self, arg=None):
        if self.current_part: self.current_part.removeNode(); self.current_part = None

    def finalize_part(self, arg=None):
        if self.current_part:
            self.assembled_parts.append(self.current_part)
            self.current_part = None


app = ModularDesignApp()
app.run()