from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    AmbientLight, DirectionalLight, LineSegs,
    ClockObject, AntialiasAttrib, TextNode, ModelPool, loadPrcFileData,
    GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    Geom, GeomTriangles, GeomNode, NodePath,
    CollisionNode, CollisionRay, CollisionHandlerQueue,
    CollisionTraverser, BitMask32, Plane, Point3, Vec3, LColor
)
from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenText, DirectLabel
import math, os, json, sqlite3, datetime, tkinter as tk
from tkinter import filedialog
import gltf

loadPrcFileData("", "load-file-type panda3d-gltf")
globalClock = ClockObject.getGlobalClock()

# ══════════════════════════════════════════════════════════
#  بناء الأشكال الهندسية
# ══════════════════════════════════════════════════════════

def _box_geom(hx, hy, hz, name):
    fmt  = GeomVertexFormat.getV3n3()
    vdat = GeomVertexData(name, fmt, Geom.UHStatic)
    vw   = GeomVertexWriter(vdat, "vertex")
    nw   = GeomVertexWriter(vdat, "normal")
    faces = [
        ([(-hx,-hy,-hz),(-hx,hy,-hz),(hx,hy,-hz),(hx,-hy,-hz)], (0,0,-1)),
        ([(-hx,-hy, hz),(hx,-hy, hz),(hx,hy, hz),(-hx,hy, hz)], (0,0, 1)),
        ([(-hx,-hy,-hz),(hx,-hy,-hz),(hx,-hy, hz),(-hx,-hy,hz)],(0,-1,0)),
        ([(-hx, hy,-hz),(-hx,hy, hz),(hx,hy, hz),(hx, hy,-hz)], (0, 1,0)),
        ([(-hx,-hy,-hz),(-hx,-hy,hz),(-hx,hy,hz),(-hx,hy,-hz)],(-1,0,0)),
        ([ (hx,-hy,-hz),(hx, hy,-hz),(hx, hy, hz),(hx,-hy, hz)], (1,0,0)),
    ]
    tris = GeomTriangles(Geom.UHStatic)
    vi = 0
    for verts, norm in faces:
        for v in verts: vw.addData3(*v); nw.addData3(*norm)
        tris.addVertices(vi,vi+1,vi+2); tris.addVertices(vi,vi+2,vi+3)
        vi += 4
    g = Geom(vdat); g.addPrimitive(tris)
    nd = GeomNode(name); nd.addGeom(g)
    return NodePath(nd)

def make_cube():     return _box_geom(.5, .5, .5,  "cube")
def make_flat_box(): return _box_geom(.5, .5, .25, "square")
def make_cuboid():   return _box_geom(1., .5, .25, "cuboid")

def make_sphere(segs=24):
    fmt  = GeomVertexFormat.getV3n3()
    vdat = GeomVertexData("sphere", fmt, Geom.UHStatic)
    vw   = GeomVertexWriter(vdat, "vertex")
    nw   = GeomVertexWriter(vdat, "normal")
    rings = segs // 2
    for r in range(rings+1):
        phi = math.pi*r/rings
        for s in range(segs+1):
            th = 2*math.pi*s/segs
            x = math.sin(phi)*math.cos(th)
            y = math.sin(phi)*math.sin(th)
            z = math.cos(phi)
            vw.addData3(x*.5,y*.5,z*.5); nw.addData3(x,y,z)
    tris = GeomTriangles(Geom.UHStatic)
    for r in range(rings):
        for s in range(segs):
            a = r*(segs+1)+s; b = a+segs+1
            tris.addVertices(a,b,a+1); tris.addVertices(a+1,b,b+1)
    g = Geom(vdat); g.addPrimitive(tris)
    nd = GeomNode("sphere"); nd.addGeom(g); return NodePath(nd)

def make_cylinder(segs=24):
    fmt  = GeomVertexFormat.getV3n3()
    vdat = GeomVertexData("cylinder", fmt, Geom.UHStatic)
    vw   = GeomVertexWriter(vdat, "vertex")
    nw   = GeomVertexWriter(vdat, "normal")
    r, h = .5, 1.0
    for i in range(segs+1):
        a = 2*math.pi*i/segs; cx,cy = math.cos(a),math.sin(a)
        for z in (0,h): vw.addData3(r*cx,r*cy,z-h/2); nw.addData3(cx,cy,0)
    tris = GeomTriangles(Geom.UHStatic)
    for i in range(segs):
        b=i*2; tris.addVertices(b,b+2,b+1); tris.addVertices(b+1,b+2,b+3)
    bc = (segs+1)*2
    vw.addData3(0,0,-h/2); nw.addData3(0,0,-1)
    for i in range(segs):
        a=2*math.pi*i/segs; vw.addData3(r*math.cos(a),r*math.sin(a),-h/2); nw.addData3(0,0,-1)
    for i in range(segs): tris.addVertices(bc,bc+1+(i+1)%segs,bc+1+i)
    tc = bc+segs+1
    vw.addData3(0,0,h/2); nw.addData3(0,0,1)
    for i in range(segs):
        a=2*math.pi*i/segs; vw.addData3(r*math.cos(a),r*math.sin(a),h/2); nw.addData3(0,0,1)
    for i in range(segs): tris.addVertices(tc,tc+1+i,tc+1+(i+1)%segs)
    g = Geom(vdat); g.addPrimitive(tris)
    nd = GeomNode("cylinder"); nd.addGeom(g); return NodePath(nd)

SHAPE_BUILDERS = {
    "Cube":     (make_cube,     0.06, 6),
    "Square":   (make_flat_box, 0.06, 6),
    "Cuboid":   (make_cuboid,   0.06, 8),
    "Sphere":   (make_sphere,   0.06, 6),
    "Cylinder": (make_cylinder, 0.05, 6),
}

# ══════════════════════════════════════════════════════════
#  قاعدة البيانات SQLite
# ══════════════════════════════════════════════════════════

DB_PATH = os.path.expanduser("~/Documents/ModularDesigns/designs.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS designs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            name      TEXT    NOT NULL,
            bam_path  TEXT    NOT NULL,
            meta_json TEXT,
            created   TEXT,
            modified  TEXT,
            thumbnail TEXT
        )
    """)
    con.commit(); con.close()

def db_save(name, bam_path, meta_json):
    init_db()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # إذا موجود نحدّث، وإلا ندرج جديد
    cur.execute("SELECT id FROM designs WHERE bam_path=?", (bam_path,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE designs SET name=?,meta_json=?,modified=? WHERE id=?",
                    (name, meta_json, now, row[0]))
    else:
        cur.execute("INSERT INTO designs(name,bam_path,meta_json,created,modified) VALUES(?,?,?,?,?)",
                    (name, bam_path, meta_json, now, now))
    con.commit(); con.close()

def db_list():
    init_db()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id,name,bam_path,modified FROM designs ORDER BY modified DESC")
    rows = cur.fetchall(); con.close()
    return rows

def db_get(design_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM designs WHERE id=?", (design_id,))
    row = cur.fetchone(); con.close()
    return row

def db_delete(design_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT bam_path FROM designs WHERE id=?", (design_id,))
    row = cur.fetchone()
    if row:
        bam = row[0]
        json_p = bam.replace(".bam","_meta.json")
        for f in [bam, json_p]:
            try: os.remove(f)
            except: pass
    cur.execute("DELETE FROM designs WHERE id=?", (design_id,))
    con.commit(); con.close()

# ══════════════════════════════════════════════════════════
#  التطبيق الرئيسي
# ══════════════════════════════════════════════════════════

class ModularDesignApp(ShowBase):
    def __init__(self):
        super().__init__()
        ModelPool.releaseAllModels()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setBackgroundColor(0.12, 0.12, 0.16)
        self.disableMouse()
        init_db()

        self._default_cam_pos = Point3(70, -140, 60)
        self.camera.setPos(self._default_cam_pos)
        self.camera.lookAt(0, 0, 0)
        self._default_cam_hpr = self.camera.getHpr()
        self.mouse_sensitivity = 0.2

        self.current_part    = None
        self.assembled_parts = []
        self.preview_models  = []
        self.groups          = []
        self._part_colors    = {}

        self.define_mode   = False
        self.defined_shape = None
        self.select_mode   = False
        self.dragging      = False
        self.drag_target   = None
        self.drag_offset   = Vec3(0,0,0)
        self.drag_plane_z  = 0.0

        self.combine_mode    = False
        self.combine_targets = []

        # ── UN: تدوير المجسم الكامل لرؤية الجهات ──────────
        self.un_mode        = False
        self.un_angle_h     = 0.0   # الدوران الأفقي
        self.un_angle_v     = 0.0   # الزاوية العمودية للكاميرا
        self.un_radius      = 80.0
        self._un_last_mouse = None

        self.view360_mode        = False
        self.view360_angle       = 0.0
        self.view360_target      = None
        self.view360_radius      = 80.0
        self.view360_height      = 40.0
        self.view360_speed       = 60.0
        self._cam_pos_before_360 = None
        self._cam_hpr_before_360 = None

        self.snap_threshold = 8.0
        self.snap_preview   = None

        self.undo_stack = []
        self.max_undo   = 25

        self.save_dir = os.path.expanduser("~/Documents/ModularDesigns")
        os.makedirs(self.save_dir, exist_ok=True)

        self.cTrav  = CollisionTraverser()
        self.cQueue = CollisionHandlerQueue()
        picker_cn   = CollisionNode("mouse_ray")
        picker_cn.setFromCollideMask(BitMask32.bit(1))
        self.picker_np  = self.camera.attachNewNode(picker_cn)
        self.picker_ray = CollisionRay()
        picker_cn.addSolid(self.picker_ray)
        self.cTrav.addCollider(self.picker_np, self.cQueue)

        self.main_menu_buttons = {}
        self.sub_menus = {}

        self.setup_lights()
        self.create_grid(200)
        self.create_center_point()
        self.create_top_libraries()
        self.create_advanced_sidebar()
        self.create_modern_color_sidebar()
        self.create_define_panel()
        self.create_combine_panel()
        self.create_view360_panel()
        self.create_smart_assistant()
        self.create_snap_indicator()
        self.create_cop_indicator()
        self.create_help_overlay()
        self.create_db_browser()

        self.accept("enter",    self.finalize_part)
        self.accept("escape",   self._handle_escape)
        self.accept("delete",   self.delete_current_part)
        self.accept("mouse1",    self.on_mouse1_press)
        self.accept("mouse1-up", self.on_mouse1_release)
        self.camera_rot_active = False
        self.accept("mouse3",    self.set_camera_rot, [True])
        self.accept("mouse3-up", self.set_camera_rot, [False])
        self.accept("v",         self.toggle_view360_mode)
        self.accept("h",         self.toggle_help_overlay)
        self.accept("f",         self.snap_to_nearest)
        self.accept("control-z", self.undo)
        self.accept("u",         self.toggle_un_mode)

        self.taskMgr.add(self.update_task, "update_task")
        self._show_assistant_msg(
            "🎉 مرحباً! H=مساعدة\n"
            "V=360°  F=دمج  U=تدوير حر  Ctrl+Z=تراجع")

    # ══════════════════════════════════════════════════════
    #  الإضاءة
    # ══════════════════════════════════════════════════════
    def setup_lights(self):
        al = AmbientLight("al"); al.setColor((.45,.45,.45,1))
        self.render.setLight(self.render.attachNewNode(al))
        dl = DirectionalLight("dl"); dl.setColor((.9,.9,.9,1))
        dn = self.render.attachNewNode(dl); dn.setHpr(45,-45,0)
        self.render.setLight(dn)
        dl2 = DirectionalLight("dl2"); dl2.setColor((.3,.3,.5,1))
        dn2 = self.render.attachNewNode(dl2); dn2.setHpr(-120,-30,0)
        self.render.setLight(dn2)

    def create_center_point(self):
        OnscreenText(text='+', pos=(0,0), scale=.06, fg=(1,1,1,.5), align=TextNode.ACenter)

    def create_grid(self, size):
        lines = LineSegs()
        for i in range(-size, size+1, 5):
            c = .35 if i%20==0 else .22
            lines.setThickness(1.2 if i%20==0 else .8)
            lines.setColor(c,c,c+.05,.25)
            lines.moveTo(i,-size,0); lines.drawTo(i,size,0)
            lines.moveTo(-size,i,0); lines.drawTo(size,i,0)
        self.render.attachNewNode(lines.create()).setTransparency(1)

    def create_snap_indicator(self):
        self.snap_label = OnscreenText(
            text="", pos=(0,-.80), scale=.045,
            fg=(.3,1,.5,1), align=TextNode.ACenter, shadow=(0,0,0,.9))
        self.snap_label.hide()

    def create_cop_indicator(self):
        self.cop_label = OnscreenText(
            text="", pos=(0,-.88), scale=.042,
            fg=(1,.7,.1,1), align=TextNode.ACenter, shadow=(0,0,0,.9))
        self.cop_label.hide()

    # ══════════════════════════════════════════════════════
    #  إدارة الألوان بدقة
    # ══════════════════════════════════════════════════════
    def _set_part_color(self, part, color):
        r,g,b,a = color[0],color[1],color[2],color[3] if len(color)>3 else 1.0
        part.setMaterialOff(1); part.setTextureOff(1)
        part.setColor(r,g,b,a); part.setColorScale(1,1,1,1)
        self._part_colors[id(part)] = (r,g,b,a)
        part.setPythonTag("base_color",(r,g,b,a))

    def _get_part_color(self, part):
        return self._part_colors.get(id(part),
               part.getPythonTag("base_color") or (1,1,1,1))

    def _restore_part_color(self, part):
        clr = self._get_part_color(part)
        try: part.setColor(*clr); part.setColorScale(1,1,1,1)
        except: pass

    def _apply_highlight(self, part, cs=(.3,1.,.45,1.)):
        part.setColorScale(*cs)

    # ══════════════════════════════════════════════════════
    #  UNDO
    # ══════════════════════════════════════════════════════
    def _save_undo_state(self, name="action"):
        all_parts = list(self.assembled_parts)
        if self.current_part and self.current_part not in all_parts:
            all_parts.append(self.current_part)
        state = []
        for p in all_parts:
            try:
                state.append({"node":p,"pos":p.getPos(),"hpr":p.getHpr(),
                               "scale":p.getScale(),"color":self._get_part_color(p),
                               "name":p.getName()})
            except: pass
        self.undo_stack.append({
            "action":name,"states":state,
            "assembled":list(self.assembled_parts),
            "groups":list(self.groups),
            "current_part":self.current_part,
            "part_colors":dict(self._part_colors)})
        if len(self.undo_stack)>self.max_undo: self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self._show_assistant_msg("⚠ لا يوجد شيء للتراجع!"); return
        last = self.undo_stack.pop()
        for s in last["states"]:
            try:
                n = s["node"]
                if not n.isEmpty():
                    n.setPos(s["pos"]); n.setHpr(s["hpr"]); n.setScale(s["scale"])
                    if s["color"]: self._set_part_color(n,s["color"])
            except: pass
        self.assembled_parts = [p for p in last["assembled"] if not p.isEmpty()]
        self.groups          = [g for g in last["groups"]    if not g.isEmpty()]
        self._part_colors    = last["part_colors"]
        cp = last["current_part"]
        self.current_part = cp if (cp and not cp.isEmpty()) else None
        self._show_assistant_msg(f"↩ تراجع عن: {last['action']} | باقي {len(self.undo_stack)}")

    # ══════════════════════════════════════════════════════
    #  ◄◄ SAVE — نافذة حفظ حقيقية ►►
    # ══════════════════════════════════════════════════════
    def export_to_file(self):
        import os
        import subprocess
        
        # 1. المسار المؤقت والنهائي
        bam_path = "D:/temp_model.bam"
        glb_path = "D:/NEURIX_FINAL.glb"
        
        try:
            all_parts = list(self.assembled_parts)
            if self.current_part: all_parts.append(self.current_part)
            
            if not all_parts: return

            # تجميع الموديل
            export_node = self.render.attachNewNode("export_node")
            for part in all_parts:
                part.copyTo(export_node)

            # 2. الحفظ بصيغة BAM (دي أكيد هتشتغل لأنها أصل الباندا)
            export_node.write_bam_file(bam_path)
            export_node.removeNode()

            # 3. استخدام أداة التحويل (نفس اللي بنكتبها في الـ Terminal بس من جوه الكود)
            # التأكد إن المكتبة موجودة
            try:
                # أمر التحويل السحري
                subprocess.run(["blend2bam", bam_path, glb_path], check=True, shell=True)
            except:
                # لو معندكش blend2bam، هنستخدم gltf-loader
                subprocess.run(["gltf-export", bam_path, glb_path], check=True, shell=True)

            # 4. التأكد والمسح
            if os.path.exists(glb_path):
                print(f"✅ أخيرااااا! الملف اتحفظ حقيقي: {glb_path}")
                os.remove(bam_path) # نمسح الملف المؤقت
                os.system(f'explorer /select,"{os.path.normpath(glb_path)}"')
            else:
                print("❌ الملف الـ GLB متخلقش، بس الـ BAM موجود في D:")

        except Exception as e:
            print(f"❌ Error: {e}")

        except Exception as e:
            print(f"❌ Error: {e}")

    # ══════════════════════════════════════════════════════
    #  ◄◄ قاعدة البيانات — نافذة عرض التصميمات ►►
    # ══════════════════════════════════════════════════════
    def create_db_browser(self):
        self.db_panel = DirectFrame(
            frameColor=(.03,.05,.12,.97),
            frameSize=(-.78,.78,-.78,.78),
            parent=self.aspect2d, pos=(0,0,0))
        self.db_panel.hide()

        OnscreenText(text="🗄  قاعدة البيانات — تصميماتك المحفوظة",
                     pos=(0,.66), scale=.048, fg=(.5,.9,1,1),
                     parent=self.db_panel, align=TextNode.ACenter)
        OnscreenText(text="انقر تصميم لفتحه وتعديله | 🗑 لحذفه",
                     pos=(0,.55), scale=.030, fg=(.7,.8,.9,1),
                     parent=self.db_panel, align=TextNode.ACenter)

        # منطقة القائمة
        self.db_list_frame = DirectFrame(
            frameColor=(.07,.07,.12,1),
            frameSize=(-.70,.70,-.36,.36),
            parent=self.db_panel, pos=(0,0,.08))

        self.db_items   = []
        self.db_scroll  = 0
        self.db_records = []

        # أزرار تحكم
        b = dict(scale=.032, parent=self.db_panel, frameSize=(-4,4,-.8,1))
        DirectButton(text="▲", pos=(-.62,0,-.36),
                     frameColor=(.2,.2,.3,1), text_fg=(1,1,1,1),
                     command=self._db_scroll, extraArgs=[-1], **b)
        DirectButton(text="▼", pos=(-.50,0,-.36),
                     frameColor=(.2,.2,.3,1), text_fg=(1,1,1,1),
                     command=self._db_scroll, extraArgs=[1], **b)
        DirectButton(text="🔄 تحديث", pos=(-.20,0,-.36),
                     frameColor=(.12,.28,.42,1), text_fg=(.6,.9,1,1),
                     command=self._db_refresh, **b)
        DirectButton(text="📁 استعراض ملف", pos=(.18,0,-.36),
                     frameColor=(.12,.35,.12,1), text_fg=(.5,1,.5,1),
                     command=self._db_browse_file, **b)
        DirectButton(text="✖ إغلاق", pos=(.55,0,-.36),
                     frameColor=(.40,.08,.08,1), text_fg=(1,.5,.5,1),
                     command=self.db_panel.hide, **b)

        self.db_status = OnscreenText(
            text="", pos=(0,-.50), scale=.028,
            fg=(.6,.7,.8,1), parent=self.db_panel, align=TextNode.ACenter)

    def open_db_browser(self):
        self.db_panel.show()
        self._db_refresh()

    def _db_refresh(self):
        for it in self.db_items:
            try: it.destroy()
            except: pass
        self.db_items  = []
        self.db_scroll = 0
        self.db_records = db_list()
        self.db_status.setText(f"📊 {len(self.db_records)} تصميم محفوظ  |  {DB_PATH}")
        self._db_draw()

    def _db_draw(self):
        for it in self.db_items:
            try: it.destroy()
            except: pass
        self.db_items = []

        y = .28
        visible = 7
        shown = self.db_records[self.db_scroll:self.db_scroll+visible]

        if not shown:
            t = OnscreenText(text="لا توجد تصميمات محفوظة بعد\nاضغط Save لحفظ تصميمك الأول!",
                             pos=(0,.05), scale=.034,
                             fg=(.6,.6,.7,1), parent=self.db_list_frame,
                             align=TextNode.ACenter)
            self.db_items.append(t); return

        for rec in shown:
            rid, rname, rbam, rmod = rec
            label = f"📐 {rname}   —   {rmod}"

            row = DirectFrame(frameColor=(.10,.14,.22,1),
                              frameSize=(-.68,.68,-.046,.046),
                              parent=self.db_list_frame, pos=(0,0,y))
            self.db_items.append(row)

            # زر الفتح
            DirectButton(text=label, scale=.028,
                         pos=(-.04,0,.005),
                         parent=row,
                         frameColor=(0,0,0,0), text_fg=(.85,.95,1,1),
                         frameSize=(-20,17,-.8,1.0),
                         command=self._db_open, extraArgs=[rid])
            # زر الحذف
            DirectButton(text="🗑", scale=.032,
                         pos=(.62,0,.005),
                         parent=row,
                         frameColor=(.40,.08,.08,1), text_fg=(1,.5,.5,1),
                         frameSize=(-1.3,1.3,-.8,.9),
                         command=self._db_delete_confirm, extraArgs=[rid, rname])
            y -= .095

    def _db_scroll(self, d):
        self.db_scroll = max(0, min(self.db_scroll+d,
                                    max(0,len(self.db_records)-7)))
        self._db_draw()

    def _db_browse_file(self):
        """فتح ملف BAM من الجهاز مباشرة"""
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost",True)
        fp = filedialog.askopenfilename(
            title="فتح تصميم محفوظ",
            initialdir=self.save_dir,
            filetypes=[("BAM 3D","*.bam"),("كل الملفات","*.*")])
        root.destroy()
        if fp: self._load_bam_file(fp)

    def _db_open(self, design_id):
        rec = db_get(design_id)
        if not rec:
            self._show_assistant_msg("❌ لم يُعثر على التصميم في قاعدة البيانات!"); return
        bam_path = rec[2]
        self.db_panel.hide()
        self._load_bam_file(bam_path, rec[4])  # rec[4] = meta_json

    def _load_bam_file(self, filepath, meta_json=None):
        if not os.path.exists(filepath):
            self._show_assistant_msg(f"❌ الملف غير موجود:\n{filepath}"); return
        try:
            # Panda3D هتحمل الـ GLB تلقائياً طالما عملنا import gltf في بداية الكود
            loaded = self.loader.loadModel(filepath, noCache=True)
            if not loaded:
                self._show_assistant_msg("❌ فشل تحميل الملف!"); return
            
            loaded.reparentTo(self.render)
            self._register_part(loaded)
            self.assembled_parts.append(loaded)
            self.current_part = loaded
            
            self._show_assistant_msg(f"✅ تم فتح: {os.path.basename(filepath)}")
        except Exception as e:
            self._show_assistant_msg(f"❌ خطأ في الفتح: {str(e)[:40]}")

    def _db_delete_confirm(self, design_id, name):
        """حذف تصميم مع تأكيد"""
        root = tk.Tk(); root.withdraw(); root.attributes("-topmost",True)
        from tkinter import messagebox
        ok = messagebox.askyesno("حذف التصميم",
                                  f"هل تريد حذف: {name}؟\nسيُحذف الملف نهائياً!")
        root.destroy()
        if ok:
            db_delete(design_id)
            self._db_refresh()
            self._show_assistant_msg(f"🗑 تم حذف: {name}")

    # ══════════════════════════════════════════════════════
    #  ◄◄ UN MODE — تدوير حر بالماوس لرؤية كل الجهات ►►
    # ══════════════════════════════════════════════════════
    def toggle_un_mode(self):
        self.un_mode = not self.un_mode
        if self.un_mode:
            # احسب مركز الكتلة والمسافة الحالية
            center = self._get_scene_center()
            cp = self.camera.getPos()
            dx,dy,dz = cp.x-center.x, cp.y-center.y, cp.z-center.z
            self.un_radius  = max(math.sqrt(dx*dx+dy*dy+dz*dz), 30.0)
            self.un_angle_h = math.degrees(math.atan2(dy, dx))
            self.un_angle_v = math.degrees(math.atan2(dz,
                              max(math.sqrt(dx*dx+dy*dy), 0.01)))
            self._un_center = center
            self._un_last_mouse = None
            self._show_assistant_msg(
                "🔄 UN Mode — تدوير حر\n"
                "اسحب بزر الماوس الأيسر لتدوير المجسم\n"
                "اضغط U مجدداً للخروج")
        else:
            self._un_last_mouse = None
            self._show_assistant_msg("⏹ خرجت من التدوير الحر")

    def _update_un_mode(self):
        """تحديث وضع UN — تدوير الكاميرا حول المجسم بالماوس"""
        if not self.un_mode: return
        if not self.mouseWatcherNode.hasMouse(): return

        md = self.win.getPointer(0)
        mx, my = md.getX(), md.getY()

        if self._un_last_mouse is not None:
            dx = mx - self._un_last_mouse[0]
            dy = my - self._un_last_mouse[1]
            self.un_angle_h -= dx * 0.4
            self.un_angle_v  = max(-85, min(85, self.un_angle_v - dy*0.4))

        self._un_last_mouse = (mx, my)

        # حساب موضع الكاميرا
        rad_h = math.radians(self.un_angle_h)
        rad_v = math.radians(self.un_angle_v)
        cos_v = math.cos(rad_v)
        cx = self._un_center.x + self.un_radius * cos_v * math.cos(rad_h)
        cy = self._un_center.y + self.un_radius * cos_v * math.sin(rad_h)
        cz = self._un_center.z + self.un_radius * math.sin(rad_v)
        self.camera.setPos(cx, cy, cz)
        self.camera.lookAt(self._un_center.x, self._un_center.y,
                           self._un_center.z)

    # ══════════════════════════════════════════════════════
    #  مكتبة الحيوانات + الأشكال
    # ══════════════════════════════════════════════════════
    def create_top_libraries(self):
        self.top_panel = DirectFrame(
            frameColor=(0,0,0,.85), frameSize=(-1.3,1.3,-.13,.13),
            parent=self.a2dTopCenter, pos=(0,0,-.15), scale=.8)
        self.top_panel.hide()
        self.animal_items = [
            ("Lion",  "Lion.glb",                          (.8,.8,.8,1)),
            ("Rabbit","White_Rabbit.glb",                  (.8,.8,.8,1)),
            ("Horse", "Basic_Chunky_Horse_Square.glb",     (.8,.8,.8,1)),
            ("B-fly", "butterfly.glb",                     (.9,.5,.9,1)),
            ("Tiger", "smilodon_or_sabre_tooth_tiger.glb", (1,.5,0,1)),
        ]
        self.animals_node = self.top_panel.attachNewNode("animals_node")
        self.shapes_node  = self.top_panel.attachNewNode("shapes_node")
        self.build_animal_items(self.animal_items, self.animals_node)
        self.build_shape_items(list(SHAPE_BUILDERS.keys()), self.shapes_node)

    def build_animal_items(self, items, parent_node):
        x_start, spacing = -.8, .45
        for i,(p_name,m_path,p_color) in enumerate(items):
            cont = parent_node.attachNewNode(f"cont_{p_name}")
            cont.setPos(x_start+i*spacing,0,0)
            try:
                model = self.loader.loadModel(m_path, noCache=True)
                model.reparentTo(cont)
                pl = m_path.lower()
                if   "butterfly" in pl: model.setScale(.015); model.setZ(-.02)
                elif "horse"     in pl: model.setScale(.02);  model.setZ(-.03)
                elif "rabbit"    in pl: model.setScale(.007); model.setZ(-.02)
                elif "tiger"     in pl: model.setScale(.008); model.setZ(-.04)
                elif "lion"      in pl: model.setScale(.005); model.setZ(-.03)
                else:                   model.setScale(.008)
                model.setColor(*p_color); self.preview_models.append(model)
                OnscreenText(text=p_name,pos=(0,-.09),scale=.035,fg=(1,1,1,1),parent=cont)
                DirectButton(parent=cont,frameColor=(0,0,0,0),
                             frameSize=(-.15,.15,-.1,.1),
                             command=self.add_animal,extraArgs=[p_name,m_path,p_color])
            except: pass

    def build_shape_items(self, shape_names, parent_node):
        x_start, spacing = -.9, .45
        clrs = [(.6,.8,1,1),(1,.8,.4,1),(.8,.5,1,1),(.4,1,.7,1),(1,.5,.5,1)]
        for i,name in enumerate(shape_names):
            cont = parent_node.attachNewNode(f"cont_{name}")
            cont.setPos(x_start+i*spacing,0,0)
            builder_fn,preview_scale,_ = SHAPE_BUILDERS[name]
            model = builder_fn(); model.reparentTo(cont)
            model.setScale(preview_scale); model.setColor(*clrs[i%len(clrs)])
            self.preview_models.append(model)
            OnscreenText(text=name,pos=(0,-.09),scale=.035,fg=(1,1,1,1),parent=cont)
            DirectButton(parent=cont,frameColor=(0,0,0,0),
                         frameSize=(-.15,.15,-.1,.1),
                         command=self.add_procedural_shape,extraArgs=[name])

    def toggle_library_tab(self, tab_type):
        if tab_type=="animals":
            if self.top_panel.isHidden() or self.animals_node.isHidden():
                self.top_panel.show(); self.animals_node.show(); self.shapes_node.hide()
            else: self.top_panel.hide()
        else:
            if self.top_panel.isHidden() or self.shapes_node.isHidden():
                self.top_panel.show(); self.shapes_node.show(); self.animals_node.hide()
            else: self.top_panel.hide()

    # ══════════════════════════════════════════════════════
    #  إضافة أشكال
    # ══════════════════════════════════════════════════════
    def finalize_part(self):
        if self.current_part:
            self._register_part(self.current_part)
            if self.current_part not in self.assembled_parts:
                self.assembled_parts.append(self.current_part)
            self.current_part = None

    def delete_current_part(self):
        if self.current_part:
            self._save_undo_state("حذف")
            if id(self.current_part) in self._part_colors:
                del self._part_colors[id(self.current_part)]
            self.current_part.removeNode()
            if self.current_part in self.assembled_parts:
                self.assembled_parts.remove(self.current_part)
            self.current_part = None
            self._show_assistant_msg("🗑 حذف — Ctrl+Z للتراجع")

    def _register_part(self, np):
        np.setCollideMask(BitMask32.bit(1))
        if id(np) not in self._part_colors:
            try:
                c = np.getColor()
                self._part_colors[id(np)] = (c[0],c[1],c[2],c[3])
                np.setPythonTag("base_color",(c[0],c[1],c[2],c[3]))
            except:
                self._part_colors[id(np)] = (1,1,1,1)
                np.setPythonTag("base_color",(1,1,1,1))

    def add_animal(self, name, path, color):
        self._save_undo_state(f"إضافة {name}")
        if self.current_part: self.finalize_part()
        try:
            self.current_part = self.loader.loadModel(path, noCache=True)
            self.current_part.reparentTo(self.render); self.current_part.setPos(0,0,5)
            pl = path.lower()
            if   "butterfly" in pl: self.current_part.setScale(1.0)
            elif "tiger"     in pl: self.current_part.setScale(1.5)
            elif "lion"      in pl: self.current_part.setScale(1.0)
            elif "rabbit"    in pl: self.current_part.setScale(4.0)
            elif "horse"     in pl: self.current_part.setScale(7.0)
            else:                   self.current_part.setScale(1)
            self._set_part_color(self.current_part,(1,1,1,1))
            self._show_assistant_msg(f"✅ {name} — Enter لتثبيته")
        except: self._show_assistant_msg(f"⚠ تعذّر تحميل {name}")

    def add_procedural_shape(self, name):
        self._save_undo_state(f"إضافة {name}")
        if self.current_part: self.finalize_part()
        builder_fn,_,scene_scale = SHAPE_BUILDERS[name]
        self.current_part = builder_fn()
        self.current_part.reparentTo(self.render)
        self.current_part.setPos(0,0,5); self.current_part.setScale(scene_scale)
        self._set_part_color(self.current_part,(1,1,1,1))
        self._show_assistant_msg(f"✅ {name} — Enter لتثبيته")

    # ══════════════════════════════════════════════════════
    #  التحديد الدقيق
    # ══════════════════════════════════════════════════════
    def _pick_shape_at_mouse(self):
        if not self.mouseWatcherNode.hasMouse(): return None
        mpos = self.mouseWatcherNode.getMouse()
        self.picker_ray.setFromLens(self.camNode, mpos.x, mpos.y)
        self.cTrav.traverse(self.render)
        if self.cQueue.getNumEntries()==0: return None
        self.cQueue.sortEntries()
        for i in range(self.cQueue.getNumEntries()):
            hit  = self.cQueue.getEntry(i).getIntoNodePath()
            node = hit
            for _ in range(30):
                if node in self.assembled_parts: return node
                if node.isEmpty() or node==self.render: break
                node = node.getParent()
        return None

    def _get_world_pos_at_mouse(self, z_level):
        if not self.mouseWatcherNode.hasMouse(): return None
        mpos = self.mouseWatcherNode.getMouse()
        near = Point3(); far = Point3()
        self.camLens.extrude(mpos,near,far)
        near_w = self.render.getRelativePoint(self.camera,near)
        far_w  = self.render.getRelativePoint(self.camera,far)
        plane  = Plane(Vec3(0,0,1),Point3(0,0,z_level))
        hit    = Point3()
        if plane.intersectsLine(hit,near_w,far_w): return hit
        return None

    # ══════════════════════════════════════════════════════
    #  COP
    # ══════════════════════════════════════════════════════
    def _get_top_z(self, part):
        try:
            b = part.getBounds(); c = part.getPos(self.render)
            return c.z + b.getRadius() * max(part.getScale())
        except: return part.getZ()

    def _check_cop_proximity(self):
        target = self.current_part or self.defined_shape
        if not target: return None,None
        tp = target.getPos(self.render)
        closest,closest_dist = None, self.snap_threshold*2
        for part in self.assembled_parts:
            if part==target: continue
            try:
                pp = part.getPos(self.render)
                dist = math.sqrt((tp.x-pp.x)**2+(tp.y-pp.y)**2)
                if dist<closest_dist: closest_dist=dist; closest=part
            except: pass
        return target,closest

    def perform_cop(self):
        mover,base = self._check_cop_proximity()
        if not mover or not base:
            self._show_assistant_msg("⚠ Cop: قرّب الشكل من الأساسي أولاً"); return
        self._save_undo_state("Cop")
        top = self._get_top_z(base)
        bnd = mover.getBounds()
        half_h = bnd.getRadius()*max(mover.getScale())
        bp = base.getPos(self.render)
        mover.setPos(bp.x,bp.y,top+half_h)
        if mover in self.assembled_parts: self.assembled_parts.remove(mover)
        if base  in self.assembled_parts: self.assembled_parts.remove(base)
        grp = self.render.attachNewNode("combined_group")
        for p in [base,mover]:
            self._restore_part_color(p); p.wrtReparentTo(grp)
        self._register_part(grp); self.groups.append(grp)
        self.assembled_parts.append(grp); self.current_part=grp
        self.cop_label.hide()
        self._show_assistant_msg("✅ Cop! التصق فوق الأساسي بدون فراغ")

    # ══════════════════════════════════════════════════════
    #  SNAP
    # ══════════════════════════════════════════════════════
    def _check_snap_proximity(self, mp):
        if not mp: return None
        mpos = mp.getPos(self.render)
        closest,closest_dist = None,self.snap_threshold
        for part in self.assembled_parts:
            if part==mp: continue
            try:
                pp = part.getPos(self.render)
                d = (mpos-pp).length()
                if d<closest_dist: closest_dist=d; closest=part
            except: pass
        return closest

    def _update_snap_feedback(self, moving_part):
        nearby = self._check_snap_proximity(moving_part)
        if self.snap_preview and self.snap_preview!=nearby:
            self._restore_part_color(self.snap_preview); self.snap_preview=None
        if nearby:
            self.snap_preview = nearby; nearby.setColorScale(1.,.9,.1,1.)
            self.snap_label.setText("🔗 F=دمج  |  Cop=إلصاق ذكي"); self.snap_label.show()
            self.cop_label.setText("📌 Cop: اضغط للإلصاق فوق الأساسي"); self.cop_label.show()
        else:
            self.snap_label.hide(); self.cop_label.hide()

    def snap_to_nearest(self):
        target = self.current_part or self.defined_shape
        if not target: self._show_assistant_msg("⚠ حدد شكلاً أولاً"); return
        nearby = self._check_snap_proximity(target)
        if not nearby: self._show_assistant_msg("⚠ لا يوجد شكل قريب كفاية"); return
        self._save_undo_state("دمج F")
        if self.current_part and self.current_part not in self.assembled_parts:
            self._register_part(self.current_part); self.assembled_parts.append(self.current_part)
        self._merge_two_parts(target,nearby)

    def _merge_two_parts(self, part_a, part_b):
        if part_b.getName().startswith("combined_group"):
            grp=part_b
            if part_a in self.assembled_parts: self.assembled_parts.remove(part_a)
            self._restore_part_color(part_a); part_a.wrtReparentTo(grp)
            if grp not in self.groups: self.groups.append(grp)
        elif part_a.getName().startswith("combined_group"):
            grp=part_a
            if part_b in self.assembled_parts: self.assembled_parts.remove(part_b)
            self._restore_part_color(part_b); part_b.wrtReparentTo(grp)
            if grp not in self.groups: self.groups.append(grp)
        else:
            grp = self.render.attachNewNode("combined_group")
            for p in [part_a,part_b]:
                self._restore_part_color(p); p.wrtReparentTo(grp)
                if p in self.assembled_parts: self.assembled_parts.remove(p)
            self._register_part(grp); self.groups.append(grp); self.assembled_parts.append(grp)
        self.snap_preview=None; self.snap_label.hide(); self.cop_label.hide()
        self.current_part=grp
        if grp not in self.assembled_parts: self.assembled_parts.append(grp)
        self._show_assistant_msg(f"✅ دمج! كتلة #{len(self.groups)}")

    # ══════════════════════════════════════════════════════
    #  DEFINE PANEL
    # ══════════════════════════════════════════════════════
    def create_define_panel(self):
        self.define_panel = DirectFrame(
            frameColor=(.04,.07,.14,.94),
            frameSize=(-.84,.84,-.16,.16),
            parent=self.a2dBottomCenter, pos=(0,0,.19))
        self.define_panel.hide()
        OnscreenText(text="🎯  Define & Select", pos=(-.66,.07), scale=.038,
                     fg=(.4,.9,1,1), parent=self.define_panel, align=TextNode.ALeft)
        self.define_status_txt = OnscreenText(
            text="انقر على أي شكل لتحديده",
            pos=(.08,.07), scale=.034, fg=(1,1,.6,1),
            parent=self.define_panel, align=TextNode.ACenter)
        self.define_info_txt = OnscreenText(
            text="", pos=(0,.00), scale=.027, fg=(.75,.85,1,1),
            parent=self.define_panel, align=TextNode.ACenter)
        btn = dict(scale=.029, parent=self.define_panel, frameSize=(-4.5,4.5,-.85,1.0))
        self.select_btn = DirectButton(
            text="🖱 Drag  OFF", pos=(-.58,0,-.105),
            frameColor=(.20,.20,.20,1), text_fg=(.9,.9,.9,1),
            command=self.toggle_select_mode, **btn)
        DirectButton(text="🔗 دمج (F)", pos=(-.18,0,-.105),
                     frameColor=(.10,.35,.15,1), text_fg=(.5,1,.6,1),
                     command=self.snap_to_nearest, **btn)
        DirectButton(text="📌 Cop", pos=(.18,0,-.105),
                     frameColor=(.40,.25,.05,1), text_fg=(1,.8,.3,1),
                     command=self.perform_cop, **btn)
        DirectButton(text="🔄 UN", pos=(.52,0,-.105),
                     frameColor=(.20,.10,.38,1), text_fg=(.8,.6,1,1),
                     command=self.toggle_un_mode, **btn)
        DirectButton(text="✖", pos=(.80,0,.07), scale=.030,
                     parent=self.define_panel,
                     frameColor=(.35,.10,.10,1), text_fg=(1,.6,.6,1),
                     frameSize=(-1.5,1.5,-.8,1.0), command=self.exit_define_mode)

    def toggle_define_mode(self):
        self.define_mode = not self.define_mode
        if self.define_mode:
            if self.combine_mode: self.exit_combine_mode()
            if self.view360_mode: self.exit_view360_mode()
            self.define_panel.show()
            self.define_status_txt.setText("انقر على أي شكل لتحديده")
            self._show_assistant_msg(
                "🎯 التحديد:\n• Drag=سحب  • F=دمج\n• Cop=إلصاق  • UN=تدوير حر")
        else: self.exit_define_mode()

    def exit_define_mode(self):
        self.define_mode=False; self.select_mode=False
        self.dragging=False; self.drag_target=None
        self._clear_defined_highlight(); self._clear_snap_preview()
        self.define_panel.hide(); self.snap_label.hide(); self.cop_label.hide()
        if hasattr(self,"select_btn"):
            self.select_btn["text"]="🖱 Drag  OFF"
            self.select_btn["frameColor"]=(.20,.20,.20,1)

    def _clear_snap_preview(self):
        if self.snap_preview:
            self._restore_part_color(self.snap_preview); self.snap_preview=None

    def _clear_defined_highlight(self):
        if self.defined_shape:
            self._restore_part_color(self.defined_shape); self.defined_shape=None

    def toggle_select_mode(self):
        self.select_mode = not self.select_mode
        if self.select_mode:
            self.select_btn["text"]="🖱 Drag  ON"
            self.select_btn["frameColor"]=(.10,.40,.20,1)
            self.define_status_txt.setText("اسحب أي شكل — 🔗 عند التقارب")
            self._show_assistant_msg("✅ السحب فعّال")
        else:
            self.select_btn["text"]="🖱 Drag  OFF"
            self.select_btn["frameColor"]=(.20,.20,.20,1)
            self.dragging=False; self.drag_target=None
            self._clear_snap_preview(); self.snap_label.hide(); self.cop_label.hide()
            self.define_status_txt.setText("انقر على أي شكل لتحديده")

    def _highlight_defined(self, target):
        self._clear_defined_highlight()
        self.defined_shape=target
        self._apply_highlight(target,(.3,1.,.45,1.))

    def _update_define_info(self, target):
        try:
            pos=target.getPos(); scl=target.getScale()
            self.define_info_txt.setText(
                f"[{target.getName()}]  "
                f"({pos.x:.1f},{pos.y:.1f},{pos.z:.1f})  scale({scl[0]:.2f})")
        except: pass

    # ══════════════════════════════════════════════════════
    #  ◄◄ COMBINE PANEL — دمج كثير بلا تعقيد ►►
    # ══════════════════════════════════════════════════════
    def create_combine_panel(self):
        self.combine_panel = DirectFrame(
            frameColor=(.04,.12,.04,.97),
            frameSize=(-.90,.90,-.26,.26),
            parent=self.a2dBottomCenter, pos=(0,0,.28))
        self.combine_panel.hide()

        OnscreenText(
            text="🔗  دمج — انقر أي أشكال من المشهد ثم ✅ OK",
            pos=(0,.17), scale=.040, fg=(.4,1,.5,1),
            parent=self.combine_panel, align=TextNode.ACenter)

        OnscreenText(
            text="① انقر شكل  ② انقر شكل آخر  ③ استمر للمزيد  ④ اضغط ✅ OK",
            pos=(0,.09), scale=.028, fg=(.8,1,.8,1),
            parent=self.combine_panel, align=TextNode.ACenter)

        self.combine_status_txt = OnscreenText(
            text="0 أشكال — انقر أي شكل لإضافته",
            pos=(0,.03), scale=.035, fg=(1,1,.4,1),
            parent=self.combine_panel, align=TextNode.ACenter)

        self.combine_info_txt = OnscreenText(
            text="", pos=(0,-.04), scale=.025, fg=(.6,.9,.6,1),
            parent=self.combine_panel, align=TextNode.ACenter)

        # ── صف الأزرار ──────────────────────────────────
        b = dict(scale=.034, parent=self.combine_panel, frameSize=(-4.2,4.2,-.85,1.))

        DirectButton(text="✅ OK دمج",
                     pos=(-.54,0,-.175), frameColor=(.05,.50,.07,1), text_fg=(.4,1,.4,1),
                     command=self.do_combine, **b)
        DirectButton(text="📌 Cop إلصاق",
                     pos=(-.16,0,-.175), frameColor=(.40,.25,.05,1), text_fg=(1,.8,.3,1),
                     command=self.cop_from_combine, **b)
        DirectButton(text="🔄 UN تدوير",
                     pos=(.22,0,-.175), frameColor=(.20,.10,.38,1), text_fg=(.8,.6,1,1),
                     command=self.toggle_un_mode, **b)
        DirectButton(text="⛓ فك أخير",
                     pos=(.58,0,-.175), frameColor=(.35,.30,.05,1), text_fg=(1,1,.4,1),
                     command=self.ungroup_last, **b)
        DirectButton(text="↩", pos=(.82,0,-.175), scale=.034,
                     parent=self.combine_panel,
                     frameColor=(.25,.10,.35,1), text_fg=(.8,.5,1,1),
                     frameSize=(-1.5,1.5,-.85,.85), command=self.undo)
        DirectButton(text="✖", pos=(.86,0,.17), scale=.032,
                     parent=self.combine_panel,
                     frameColor=(.40,.10,.10,1), text_fg=(1,.6,.6,1),
                     frameSize=(-1.5,1.5,-.8,1.), command=self.exit_combine_mode)

    def toggle_combine_mode(self):
        self.combine_mode = not self.combine_mode
        if self.combine_mode:
            if self.define_mode: self.exit_define_mode()
            if self.view360_mode: self.exit_view360_mode()
            self.combine_panel.show()
            self.combine_targets=[]
            self._refresh_combine_status()
            self._show_assistant_msg(
                "🔗 الدمج:\n"
                "① انقر أي شكل من المشهد\n"
                "② يتحول برتقالي — تابع للمزيد\n"
                "③ اضغط ✅ OK — يدمجان ككتلة\n"
                "🔄 UN = تدوير حر للمجسم")
        else: self.exit_combine_mode()

    def exit_combine_mode(self):
        self.combine_mode=False
        for p in self.combine_targets: self._restore_part_color(p)
        self.combine_targets=[]; self.combine_panel.hide()

    def _refresh_combine_status(self):
        n = len(self.combine_targets)
        if n==0:
            self.combine_status_txt.setText("0 أشكال — انقر أي شكل لإضافته")
            self.combine_info_txt.setText("")
        else:
            names = " + ".join([p.getName()[:8] for p in self.combine_targets])
            self.combine_status_txt.setText(f"✔  {n} أشكال — اضغط OK لدمجها!")
            self.combine_info_txt.setText(names[:60])

    def do_combine(self):
        """دمج كل الأشكال المحددة ككتلة واحدة"""
        if len(self.combine_targets)<2:
            self.combine_status_txt.setText("⚠ انقر على شكلين على الأقل!"); return
        self._save_undo_state("دمج")
        grp = self.render.attachNewNode("combined_group")
        for part in self.combine_targets:
            self._restore_part_color(part)
            part.wrtReparentTo(grp)
            if part in self.assembled_parts: self.assembled_parts.remove(part)
        self._register_part(grp)
        self.groups.append(grp); self.assembled_parts.append(grp)
        self.current_part=grp; self.combine_targets=[]
        self.combine_status_txt.setText(f"✅ كتلة #{len(self.groups)} — تتحرك معاً")
        self.combine_info_txt.setText("استخدم Move أو Drag — UN لرؤية كل الجهات")
        self._show_assistant_msg(
            f"✅ دمج كتلة #{len(self.groups)}!\n"
            f"اضغط 🔄 UN لتدوير المجسم ورؤية كل جهاته\n"
            f"ثم أضف المزيد من الأشكال")

    def cop_from_combine(self):
        if len(self.combine_targets)<2:
            self.combine_status_txt.setText("⚠ انقر على شكلين أولاً!"); return
        self._save_undo_state("Cop")
        mover=self.combine_targets[0]; base=self.combine_targets[1]
        top=self._get_top_z(base); b=mover.getBounds()
        half_h=b.getRadius()*max(mover.getScale())
        bp=base.getPos(self.render)
        mover.setPos(bp.x,bp.y,top+half_h)
        grp=self.render.attachNewNode("combined_group")
        for p in [base,mover]:
            self._restore_part_color(p); p.wrtReparentTo(grp)
            if p in self.assembled_parts: self.assembled_parts.remove(p)
        self._register_part(grp); self.groups.append(grp); self.assembled_parts.append(grp)
        self.current_part=grp; self.combine_targets=[]
        self.combine_status_txt.setText("✅ Cop — ملتصق بدون فراغ")
        self._show_assistant_msg("📌 Cop! فوق الأساسي — اضغط UN لرؤية الجهات")

    def ungroup_last(self):
        if not self.groups:
            self.combine_status_txt.setText("⚠ لا توجد مجموعات!"); return
        self._save_undo_state("فك الدمج")
        grp=self.groups.pop()
        for ch in list(grp.getChildren()):
            ch.wrtReparentTo(self.render); self._register_part(ch); self.assembled_parts.append(ch)
        if grp in self.assembled_parts: self.assembled_parts.remove(grp)
        grp.removeNode()
        self.combine_status_txt.setText(f"✅ فك الدمج — متبقي: {len(self.groups)}")
        self._show_assistant_msg("⛓ فك الدمج — Ctrl+Z للتراجع")

    # ══════════════════════════════════════════════════════
    #  360° VIEW
    # ══════════════════════════════════════════════════════
    def create_view360_panel(self):
        self.view360_panel = DirectFrame(
            frameColor=(.08,.04,.14,.96),
            frameSize=(-.72,.72,-.13,.13),
            parent=self.a2dBottomCenter, pos=(0,0,.16))
        self.view360_panel.hide()
        OnscreenText(text="🌀  360° View", pos=(-.54,.05), scale=.040,
                     fg=(.8,.5,1,1), parent=self.view360_panel, align=TextNode.ALeft)
        b = dict(scale=.033, parent=self.view360_panel, frameSize=(-3.8,3.8,-.8,1.))
        self.speed_label = DirectButton(
            text="▶ عادي", pos=(-.44,0,-.075),
            frameColor=(.20,.15,.30,1), text_fg=(.9,.7,1,1),
            command=self._cycle_view_speed, **b)
        DirectButton(text="🎯 تركيز", pos=(.0,0,-.075),
                     frameColor=(.25,.15,.35,1), text_fg=(.8,.6,1,1),
                     command=self._view360_focus_selected, **b)
        DirectButton(text="⏹ إيقاف وعودة", pos=(.48,0,-.075),
                     frameColor=(.35,.10,.10,1), text_fg=(1,.6,.6,1),
                     command=self.exit_view360_mode, **b)
        self._view_speeds=[20,60,120]; self._view_speed_idx=1

    def toggle_view360_mode(self):
        self.view360_mode = not self.view360_mode
        if self.view360_mode:
            if self.define_mode: self.exit_define_mode()
            if self.combine_mode: self.exit_combine_mode()
            self._cam_pos_before_360=self.camera.getPos()
            self._cam_hpr_before_360=self.camera.getHpr()
            self.view360_target=self._get_scene_center()
            cp=self.camera.getPos(); t=self.view360_target
            dx,dy=cp.x-t.x,cp.y-t.y
            self.view360_radius=max(math.sqrt(dx*dx+dy*dy),40.)
            self.view360_height=max(cp.z,25.)
            self.view360_angle=math.degrees(math.atan2(dy,dx))
            self.view360_panel.show()
            self._show_assistant_msg("🌀 عرض 360° — ⏹ للعودة لمكانك")
        else: self.exit_view360_mode()

    def exit_view360_mode(self):
        self.view360_mode=False; self.view360_panel.hide()
        if self._cam_pos_before_360 is not None:
            self.camera.setPos(self._cam_pos_before_360)
            self.camera.setHpr(self._cam_hpr_before_360)
            self._cam_pos_before_360=None; self._cam_hpr_before_360=None
        self._show_assistant_msg("⏹ عدت لمكانك السابق")

    def _get_scene_center(self):
        all_parts=list(self.assembled_parts)
        if self.current_part: all_parts.append(self.current_part)
        if not all_parts: return Point3(0,0,0)
        cx=cy=cz=cnt=0
        for p in all_parts:
            try:
                pos=p.getPos(self.render); cx+=pos.x; cy+=pos.y; cz+=pos.z; cnt+=1
            except: pass
        return Point3(cx/cnt,cy/cnt,cz/cnt) if cnt else Point3(0,0,0)

    def _cycle_view_speed(self):
        self._view_speed_idx=(self._view_speed_idx+1)%3
        self.view360_speed=self._view_speeds[self._view_speed_idx]
        self.speed_label["text"]=["🐢 بطيء","▶ عادي","⚡ سريع"][self._view_speed_idx]

    def _view360_focus_selected(self):
        t=self.current_part or self.defined_shape
        if t:
            try:
                self.view360_target=t.getPos(self.render)
                self._show_assistant_msg(f"🎯 تركيز: {t.getName()}")
            except: pass
        else: self.view360_target=self._get_scene_center()

    def _update_view360(self, dt):
        self.view360_angle+=self.view360_speed*dt
        if self.view360_angle>=360: self.view360_angle-=360
        rad=math.radians(self.view360_angle); t=self.view360_target or Point3(0,0,0)
        self.camera.setPos(t.x+self.view360_radius*math.cos(rad),
                           t.y+self.view360_radius*math.sin(rad), self.view360_height)
        self.camera.lookAt(t.x,t.y,t.z+5)

    # ══════════════════════════════════════════════════════
    #  SMART ASSISTANT
    # ══════════════════════════════════════════════════════
    def create_smart_assistant(self):
        self.assistant_frame = DirectFrame(
            frameColor=(.04,.04,.10,.93),
            frameSize=(-.52,.52,-.15,.15),
            parent=self.a2dBottomRight, pos=(-.57,0,.22))
        self.assistant_text = OnscreenText(
            text="", pos=(0,.04), scale=.029,
            fg=(.85,.95,1,1), parent=self.assistant_frame,
            align=TextNode.ACenter, wordwrap=26)
        self.assistant_frame.hide(); self._assistant_timer=0

    def _show_assistant_msg(self, msg, duration=5.0):
        self.assistant_text.setText(msg)
        self.assistant_frame.show(); self._assistant_timer=duration

    def _update_assistant(self, dt):
        if not self.assistant_frame.isHidden():
            self._assistant_timer-=dt
            if self._assistant_timer<=0: self.assistant_frame.hide()

    # ══════════════════════════════════════════════════════
    #  HELP OVERLAY
    # ══════════════════════════════════════════════════════
    def create_help_overlay(self):
        self.help_overlay = DirectFrame(
            frameColor=(0,0,0,.93),
            frameSize=(-.80,.80,-.94,.94),
            parent=self.aspect2d, pos=(0,0,0))
        self.help_overlay.hide()
        OnscreenText(text="📖  دليل الاستخدام الكامل", pos=(0,.80), scale=.050,
                     fg=(.5,.9,1,1), parent=self.help_overlay, align=TextNode.ACenter)
        lines = [
            ("🎮 التحكم الأساسي", (.9,.9,.4,1)),
            ("  زر الماوس الأيمن + سحب = دوران الكاميرا", (1,1,1,1)),
            ("  Enter = تثبيت  |  Delete = حذف  |  Ctrl+Z = تراجع", (1,1,1,1)),
            ("", (1,1,1,0)),
            ("🎯 التحديد الدقيق", (.4,1,.6,1)),
            ("  Define → انقر شكل لتحديده (أخضر)", (1,1,1,1)),
            ("  Drag ON → اسحب الأشكال بحرية كاملة", (1,1,1,1)),
            ("", (1,1,1,0)),
            ("🔗 الدمج — سهل ومرن", (.8,.5,1,1)),
            ("  Combine → انقر ① ② ③ ... → ✅ OK", (1,1,1,1)),
            ("  يمكن دمج أي عدد من الأشكال دفعة واحدة!", (.7,1,.7,1)),
            ("  انقر نفس الشكل مجدداً لإلغاء تحديده", (.8,.8,.8,1)),
            ("", (1,1,1,0)),
            ("🔄 UN — تدوير حر لرؤية كل الجهات", (.8,.6,1,1)),
            ("  U أو زر UN = تدوير حر بزر الماوس الأيسر", (1,1,1,1)),
            ("  مفيد لرؤية الجزء الخلفي قبل الدمج", (.9,1,.8,1)),
            ("  U مرة أخرى للخروج من وضع التدوير", (.8,.8,.8,1)),
            ("", (1,1,1,0)),
            ("📌 Cop = إلصاق ذكي بدون فراغ", (1,.8,.3,1)),
            ("  قرّب الشكل من الأساسي → اضغط Cop", (1,1,1,1)),
            ("", (1,1,1,0)),
            ("💾 الحفظ وقاعدة البيانات", (1,.7,.4,1)),
            ("  Save = نافذة حفظ على جهازك + قاعدة البيانات", (1,1,1,1)),
            ("  DB Browser = عرض كل تصميماتك المحفوظة", (1,1,1,1)),
            ("  انقر تصميم لفتحه وتعديله | 🗑 لحذفه", (.9,.9,1,1)),
            ("  🌀 V = عرض 360°  |  ⏹ = عودة لمكانك", (1,1,1,1)),
        ]
        y=.68
        for line,color in lines:
            OnscreenText(text=line, pos=(-.74,y), scale=.026,
                         fg=color, parent=self.help_overlay, align=TextNode.ALeft)
            y-=.055
        DirectButton(text="✖ إغلاق (H)", scale=.042, pos=(0,0,-.86),
                     parent=self.help_overlay, frameColor=(.35,.10,.10,1),
                     text_fg=(1,.6,.6,1), frameSize=(-4,4,-.8,1.),
                     command=self.help_overlay.hide)

    def toggle_help_overlay(self):
        if self.help_overlay.isHidden(): self.help_overlay.show()
        else: self.help_overlay.hide()

    # ══════════════════════════════════════════════════════
    #  شريط الألوان
    # ══════════════════════════════════════════════════════
    def create_modern_color_sidebar(self):
        self.color_sidebar = DirectFrame(
            frameColor=(.05,.05,.08,.90),
            frameSize=(-.10,.10,-1.2,1.2),
            parent=self.a2dRightCenter, pos=(-.10,0,0))
        OnscreenText(text="Colors", pos=(0,.95), scale=.048,
                     fg=(.8,.9,1,1), parent=self.color_sidebar, align=TextNode.ACenter)
        colors = [
            (1.,0.,0.,1),(0.,.9,0.,1),(0.,.2,1.,1),(1.,1.,0.,1),(1.,.5,0.,1),
            (1.,0.,1.,1),(0.,1.,1.,1),(.5,0.,.8,1),(0.,0.,.6,1),(1.,1.,1.,1),
            (.6,.6,.6,1),(.15,.15,.15,1),(1.,.8,.6,1),(.5,.25,0.,1),(.2,.7,.4,1),
            (1.,.6,.8,1),(.7,.9,.2,1),(.3,.15,.6,1),
        ]
        y=.85
        for clr in colors:
            DirectButton(parent=self.color_sidebar, frameColor=clr,
                         frameSize=(-.045,.045,-.045,.045), pos=(0,0,y),
                         command=self.change_color, extraArgs=[clr])
            y-=.10
        self.color_sidebar.hide()

    def toggle_color_sidebar(self):
        if self.color_sidebar.isHidden(): self.color_sidebar.show()
        else: self.color_sidebar.hide()

    def change_color(self, color):
        target=self.current_part
        if not target:
            self._show_assistant_msg("⚠ حدد شكلاً أولاً"); return
        self._save_undo_state("لون")
        self._set_part_color(target,color)
        if self.defined_shape==target:
            self._apply_highlight(target,(.3,1.,.45,1.))
        self._show_assistant_msg("🎨 اللون تغيّر — كل شكل بلونه المستقل")

    # ══════════════════════════════════════════════════════
    #  الشريط الجانبي الأيسر
    # ══════════════════════════════════════════════════════
    def create_advanced_sidebar(self):
        self.side_bar = DirectFrame(
            frameColor=(.08,.08,.12,.94),
            frameSize=(-.18,.18,-1,1),
            parent=self.a2dLeftCenter, pos=(.18,0,0))
        self.menu_data = [
            ("Models",    ["Toggle Animals"]),
            ("Shapes",    ["Toggle Shapes"]),
            ("Colors",    ["Toggle Colors"]),
            ("Define",    ["Defining Shape"]),
            ("Combine",   ["Combining Shapes"]),
            ("View",      ["View 360°","UN تدوير","Help Guide"]),
            ("Edit",      ["Undo","Fix Part","Clear All"]),
            ("Save",      ["Save Design","DB Browser"]),
            ("Dimensions",["W+","W-","L+","L-","H+","H-"]),
            ("Move",      ["Up (Z+)","Down (Z-)","Right (X+)","Left (X-)","Forward (Y+)","Back (Y-)","Up Up"]),
            ("Zoom",      ["In (+)","Out (-)"]),
            ("Rotate",    ["Rot H+","Rot H-","Rot P+","Rot P-","Rot R+","Rot R-"]),
            ("Select",    ["Delete Part"]),
        ]
        for name,options in self.menu_data:
            btn = DirectButton(
                text=name, scale=.047, parent=self.side_bar,
                frameColor=(.22,.22,.28,1), text_fg=(1,1,1,1),
                command=self.toggle_menu, extraArgs=[name])
            self.main_menu_buttons[name]=btn
            sub_frame=DirectFrame(parent=self.side_bar, frameColor=(0,0,0,0))
            self.sub_menus[name]=sub_frame
            sy=-.08
            for opt in options:
                if   opt=="Toggle Animals":   cmd,args=lambda: self.toggle_library_tab("animals"),[]
                elif opt=="Toggle Shapes":    cmd,args=lambda: self.toggle_library_tab("shapes"),[]
                elif opt=="Toggle Colors":    cmd,args=self.toggle_color_sidebar,[]
                elif opt=="Defining Shape":   cmd,args=self.toggle_define_mode,[]
                elif opt=="Combining Shapes": cmd,args=self.toggle_combine_mode,[]
                elif opt=="View 360°":        cmd,args=self.toggle_view360_mode,[]
                elif opt=="UN تدوير":         cmd,args=self.toggle_un_mode,[]
                elif opt=="Help Guide":       cmd,args=self.toggle_help_overlay,[]
                elif opt=="Save Design":      cmd,args=self.export_to_file,[]
                elif opt=="DB Browser":       cmd,args=self.open_db_browser,[]
                elif opt=="Undo":             cmd,args=self.undo,[]
                else:                         cmd,args=self.handle_action,[opt]

                if   opt=="Defining Shape":   fc=(.12,.30,.48,1)
                elif opt=="Combining Shapes": fc=(.28,.15,.42,1)
                elif opt=="View 360°":        fc=(.25,.10,.40,1)
                elif opt=="UN تدوير":         fc=(.20,.10,.38,1)
                elif opt=="Help Guide":       fc=(.10,.25,.35,1)
                elif opt=="Save Design":      fc=(.08,.45,.12,1)
                elif opt=="DB Browser":       fc=(.05,.28,.40,1)
                elif opt=="Undo":             fc=(.28,.10,.40,1)
                elif "W" in opt or "L" in opt or "H" in opt: fc=(.45,.25,.08,1)
                elif opt=="Up Up":            fc=(.35,.15,.70,1)
                elif opt=="Clear All":        fc=(.50,.08,.08,1)
                else:                         fc=(.18,.35,.55,1)

                DirectButton(
                    text=opt, scale=.033, pos=(0,0,sy),
                    parent=sub_frame, frameColor=fc,
                    text_fg=(1,1,1,1), frameSize=(-3.5,3.5,-.6,.8),
                    command=cmd, extraArgs=args)
                sy-=.105
            sub_frame.hide()
        self.reposition_menus()

    def reposition_menus(self):
        y=.95
        for name,options in self.menu_data:
            self.main_menu_buttons[name].setPos(0,0,y)
            self.sub_menus[name].setPos(0,0,y)
            y-=((len(options)*.105)+.15) if not self.sub_menus[name].isHidden() else .13

    def toggle_menu(self, menu_name):
        for name,frame in self.sub_menus.items():
            if name==menu_name:
                if frame.isHidden(): frame.show()
                else: frame.hide()
            else: frame.hide()
        self.reposition_menus()

    # ══════════════════════════════════════════════════════
    #  handle_action
    # ══════════════════════════════════════════════════════
    def handle_action(self, action):
        if action=="Clear All":
            self._save_undo_state("مسح الكل")
            for p in self.assembled_parts:
                try: p.removeNode()
                except: pass
            self.assembled_parts=[]; self.groups=[]
            if self.current_part:
                try: self.current_part.removeNode()
                except: pass
                self.current_part=None
            self._part_colors.clear()
            self._show_assistant_msg("🗑 مسح الكل — Ctrl+Z للتراجع"); return
        if not self.current_part: return
        self._save_undo_state(action)
        p=self.current_part
        if   action=="Up Up":        p.setZ(p.getZ()+10.)
        elif action=="Up (Z+)":      p.setZ(p.getZ()+1)
        elif action=="Down (Z-)":    p.setZ(p.getZ()-1)
        elif action=="Right (X+)":   p.setX(p.getX()+1)
        elif action=="Left (X-)":    p.setX(p.getX()-1)
        elif action=="Forward (Y+)": p.setY(p.getY()+1)
        elif action=="Back (Y-)":    p.setY(p.getY()-1)
        elif action=="In (+)":       p.setScale(p.getScale()*1.1)
        elif action=="Out (-)":      p.setScale(p.getScale()/1.1)
        elif action=="Rot H+": p.setH(p.getH()+5)
        elif action=="Rot H-": p.setH(p.getH()-5)
        elif action=="Rot P+": p.setP(p.getP()+5)
        elif action=="Rot P-": p.setP(p.getP()-5)
        elif action=="Rot R+": p.setR(p.getR()+5)
        elif action=="Rot R-": p.setR(p.getR()-5)
        elif action=="W+": p.setSx(p.getSx()*1.1)
        elif action=="W-": p.setSx(p.getSx()/1.1)
        elif action=="L+": p.setSy(p.getSy()*1.1)
        elif action=="L-": p.setSy(p.getSy()/1.1)
        elif action=="H+": p.setSz(p.getSz()*1.1)
        elif action=="H-": p.setSz(p.getSz()/1.1)
        elif action=="Fix Part":    self.finalize_part()
        elif action=="Delete Part": self.delete_current_part()
        if self.define_mode and self.defined_shape: self._update_define_info(p)
        if self.select_mode or self.define_mode: self._update_snap_feedback(p)

    # ══════════════════════════════════════════════════════
    #  أحداث الماوس
    # ══════════════════════════════════════════════════════
    def on_mouse1_press(self):
        if self.view360_mode: return
        if self.un_mode: return   # في UN يتحكم الزر الأيسر بالتدوير

        if self.define_mode and self.select_mode:
            target=self._pick_shape_at_mouse()
            if target:
                self.dragging=True; self.drag_target=target
                self.drag_plane_z=target.getZ()
                hp=self._get_world_pos_at_mouse(self.drag_plane_z)
                if hp: self.drag_offset=target.getPos()-hp
                self._highlight_defined(target)
                if self.current_part and self.current_part!=target: self.finalize_part()
                if target in self.assembled_parts: self.assembled_parts.remove(target)
                self.current_part=target
            return

        if self.define_mode and not self.select_mode:
            target=self._pick_shape_at_mouse()
            if target is None: return
            self._highlight_defined(target)
            if self.current_part and self.current_part!=target: self.finalize_part()
            if target in self.assembled_parts: self.assembled_parts.remove(target)
            self.current_part=target
            self.define_status_txt.setText(f"🎯  [{target.getName()}]")
            self._update_define_info(target); return

        if self.combine_mode:
            target=self._pick_shape_at_mouse()
            if target is None: return
            if target in self.combine_targets:
                self.combine_targets.remove(target)
                self._restore_part_color(target)
            else:
                self.combine_targets.append(target)
                target.setColorScale(1.,.55,.1,1.)
            self._refresh_combine_status()

    def on_mouse1_release(self):
        if self.dragging:
            self.dragging=False
            if self.drag_target: self._update_define_info(self.drag_target)

    def set_camera_rot(self, active):
        self.camera_rot_active=active

    def _handle_escape(self):
        if not self.help_overlay.isHidden(): self.help_overlay.hide(); return
        if not self.db_panel.isHidden(): self.db_panel.hide(); return
        if self.un_mode: self.toggle_un_mode(); return
        if self.view360_mode: self.exit_view360_mode(); return
        if self.define_mode: self.exit_define_mode(); return
        if self.combine_mode: self.exit_combine_mode(); return
        self.finalize_part()

    # ══════════════════════════════════════════════════════
    #  حلقة التحديث
    # ══════════════════════════════════════════════════════
    def update_task(self, task):
        dt=globalClock.getDt()

        # دوران الكاميرا اليدوي (زر الماوس الأيمن)
        if self.camera_rot_active and not self.view360_mode and \
           not self.un_mode and self.mouseWatcherNode.hasMouse():
            md=self.win.getPointer(0); x,y=md.getX(),md.getY()
            if hasattr(self,'last_mouse_pos'):
                dx=x-self.last_mouse_pos[0]; dy=y-self.last_mouse_pos[1]
                self.camera.setH(self.camera.getH()-dx*self.mouse_sensitivity)
                self.camera.setP(self.camera.getP()-dy*self.mouse_sensitivity)
            self.last_mouse_pos=(x,y)
        else:
            if hasattr(self,'last_mouse_pos') and not self.view360_mode and not self.un_mode:
                del self.last_mouse_pos

        # 360° تلقائي
        if self.view360_mode: self._update_view360(dt)

        # UN — تدوير حر بزر الماوس الأيسر
        if self.un_mode:
            if self.mouseWatcherNode.hasMouse():
                from panda3d.core import MouseButton
                # نستخدم is_button_down لفحص الزر الأيسر
                left_down = self.mouseWatcherNode.isButtonDown(
                    self.mouseWatcherNode.getButton("mouse1") if hasattr(
                        self.mouseWatcherNode,"getButton") else 0)
                # بديل: نتحقق من الضغط عبر is_button_down
                try:
                    from panda3d.core import MouseButton
                    left_down = self.mouseWatcherNode.isButtonDown(MouseButton.one())
                except: left_down = True  # افتراضي: شغّال دائماً
                if left_down:
                    self._update_un_mode()
                else:
                    self._un_last_mouse = None

        # السحب
        if self.dragging and self.drag_target and self.mouseWatcherNode.hasMouse():
            np=self._get_world_pos_at_mouse(self.drag_plane_z)
            if np:
                self.drag_target.setPos(np+self.drag_offset)
                self._update_define_info(self.drag_target)
                self._update_snap_feedback(self.drag_target)

        # دوران معاينة الأشكال
        for m in self.preview_models:
            if not m.isEmpty(): m.setH(m.getH()+40*dt)

        self._update_assistant(dt)
        return task.cont


app = ModularDesignApp()
app.run()