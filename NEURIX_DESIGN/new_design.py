from panda3d.core import loadPrcFileData
loadPrcFileData("", "load-display pandadx9")   # DirectX 9 بدل OpenGL
loadPrcFileData("", "aux-display pandagl")      # fallback لو DX9 مش موجود

from direct.showbase.ShowBase import ShowBase
from panda3d.core import (AmbientLight, DirectionalLight, LineSegs,
                          WindowProperties, ClockObject, AntialiasAttrib, TextNode)
from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenText
import threading, cv2, mediapipe as mp, numpy as np
import pyautogui, math, time

globalClock = ClockObject.getGlobalClock()
pyautogui.FAILSAFE = False
pyautogui.PAUSE    = 0

# ══════════════════════════════════════════════════════════════════════
#  SHARED GESTURE STATE  (Panda3D main thread ←→ OpenCV gesture thread)
# ══════════════════════════════════════════════════════════════════════
GS = {
    'mode':        None,
    'fist_stop':   False,    # None | 'rotate' | 'move' | 'zoom'
    # rotate
    'rot_x':       0.0,
    'rot_y':       0.0,
    'ctrl_active': False,
    # move
    'move_x':      0.0,
    'move_z':      0.0,
    'grabbing':    False,
    # zoom
    'zoom_scale':  3.0,
    'prev_pinch':  None,
}
gs_lock   = threading.Lock()
stop_flag = threading.Event()


# ══════════════════════════════════════════════════════════════════════
#  GESTURE WORKER THREAD
#  ► Air Click  : cursor = index tip  |  pinch click (only when mode=None)
#  ► Rotate     : index-up gesture    → rot_x / rot_y
#  ► Move       : tight pinch         → move_x / move_z
#  ► Zoom       : pinch delta         → zoom_scale
# ══════════════════════════════════════════════════════════════════════
def gesture_worker():
    mpm   = mp.solutions.hands
    hands = mpm.Hands(model_complexity=0, max_num_hands=1,
                      min_detection_confidence=0.8,
                      min_tracking_confidence=0.75)

    cap = cv2.VideoCapture(0)
    cw  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    ch  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sw, sh = pyautogui.size()

    # air-click smoothing vars (double-layer EMA)
    smx,  smy  = float(sw // 2), float(sh // 2)   # layer 1
    smx2, smy2 = float(sw // 2), float(sh // 2)   # layer 2
    pmx,  pmy  = sw // 2, sh // 2
    last_click_t = 0
    is_clicking  = False

    SMOOTH  = 0.10     # ↓ أبطأ = أكثر ثبات (كان 0.7)
    SMOOTH2 = 0.15     # طبقة ثانية من التنعيم
    DZ      = 30       # ↑ dead zone أكبر = أقل رعشة (كان 15)
    COOL    = 0.6      # click cooldown seconds
    CTH     = 38       # click threshold pixels

    GOLD    = (40, 190, 240)
    MOVE_C  = (0, 220, 120)
    ZOOM_C  = (255, 165, 0)
    ROTATE_C= (180, 80, 255)
    MODE_COLORS = {'rotate': ROTATE_C, 'move': MOVE_C, 'zoom': ZOOM_C}

    while not stop_flag.is_set():
        ret, frame = cap.read()
        if not ret:
            continue

        frame  = cv2.flip(frame, 1)
        result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        now    = time.time()

        with gs_lock:
            mode = GS['mode']

        if result.multi_hand_landmarks:
            lms = result.multi_hand_landmarks[0].landmark
            t8  = lms[8]   # index tip
            t4  = lms[4]   # thumb tip

            # ── pixel coords ────────────────────────────────────
            x8p = int(t8.x * cw);  y8p = int(t8.y * ch)
            x4p = int(t4.x * cw);  y4p = int(t4.y * ch)
            pdist = math.hypot(x8p - x4p, y8p - y4p)

            # ── Air Click: cursor always follows index tip ───────
            nsx = int(np.interp(x8p, [0, cw], [0, sw]))
            nsy = int(np.interp(y8p, [0, ch], [0, sh]))
            nsx = nsx if abs(nsx - pmx) > DZ else pmx
            nsy = nsy if abs(nsy - pmy) > DZ else pmy
            pmx, pmy = nsx, nsy
            # ── Double-layer EMA: layer1 → layer2 ────────────────
            smx  += SMOOTH  * (nsx  - smx)
            smy  += SMOOTH  * (nsy  - smy)
            smx2 += SMOOTH2 * (smx  - smx2)
            smy2 += SMOOTH2 * (smy  - smy2)
            pyautogui.moveTo(int(smx2), int(smy2), duration=0)

            # ── Click: press on touch, release on open (instant) ─
            if mode is None:
                pinching = pdist < CTH
                if pinching and not is_clicking:
                    # اول لحظة لمس - mouseDown فورا
                    pyautogui.mouseDown()
                    is_clicking  = True
                    last_click_t = now
                elif not pinching and is_clicking:
                    # انفصلوا - mouseUp فورا
                    pyautogui.mouseUp()
                    is_clicking = False
            else:
                if is_clicking:
                    pyautogui.mouseUp()
                    is_clicking = False

            # ── Fist = Stop gesture mode ─────────────────────────
            # قبضة: كل الأصابع الـ 4 مقفولة (tips أسفل من knuckles)
            is_fist = all(
                lms[tip].y > lms[knuckle].y
                for tip, knuckle in [(8,6),(12,10),(16,14),(20,18)]
            )
            if is_fist and mode is not None:
                with gs_lock:
                    GS['mode']        = None
                    GS['ctrl_active'] = False
                    GS['grabbing']    = False
                    GS['prev_pinch']  = None
                    GS['fist_stop']   = True   # علامة للـ Panda3D يحدث UI
                mode = None   # تحديث المتغير المحلي فوراً

            # ── Gesture Modes ────────────────────────────────────
            with gs_lock:
                if mode == 'rotate':
                    # gesture: index finger up, rest curled
                    idx_up    = lms[8].y < lms[6].y
                    rest_down = all(lms[t].y > lms[p].y
                                    for t, p in [(12,10),(16,14),(20,18)])
                    if idx_up and rest_down:
                        GS['rot_x']       = (lms[8].y - 0.5) * -360
                        GS['rot_y']       = (lms[8].x - 0.5) *  360
                        GS['ctrl_active'] = True
                    else:
                        GS['ctrl_active'] = False

                elif mode == 'move':
                    # gesture: tight pinch moves object
                    nd = math.hypot(t4.x - t8.x, t4.y - t8.y)
                    if nd < 0.055:
                        GS['move_x']   = (t8.x - 0.5) *  100
                        GS['move_z']   = (t8.y - 0.5) * -80
                        GS['grabbing'] = True
                    else:
                        GS['grabbing'] = False

                elif mode == 'zoom':
                    # gesture: pinch open/close changes scale
                    nd = math.hypot(t4.x - t8.x, t4.y - t8.y)
                    if GS['prev_pinch'] is not None:
                        delta = nd - GS['prev_pinch']
                        GS['zoom_scale'] = max(0.3, GS['zoom_scale'] + delta * 30)
                    GS['prev_pinch'] = nd

            # ── Draw landmarks on cam preview ────────────────────
            col = MODE_COLORS.get(mode, GOLD)
            mp.solutions.drawing_utils.draw_landmarks(
                frame, result.multi_hand_landmarks[0],
                mpm.HAND_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=col, thickness=2),
                mp.solutions.drawing_utils.DrawingSpec(color=col, thickness=2))

            # pinch line
            cv2.line(frame, (x8p, y8p), (x4p, y4p), col, 2)

            # fist flash
            if is_fist and mode is None:
                cv2.putText(frame, "STOPPED!", (cw//2-80, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0,80,255), 3)

            # click flash
            if is_clicking:
                cv2.putText(frame, "CLICK!", (cw//2-60, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0,255,80), 3)

        else:
            # no hand → reset pinch baseline
            with gs_lock:
                if GS['mode'] == 'zoom':
                    GS['prev_pinch'] = None

        # ── HUD overlay ─────────────────────────────────────────
        mode_lbl  = mode.upper() if mode else "AIR CLICK"
        hud_color = MODE_COLORS.get(mode, GOLD)
        cv2.putText(frame, f"Mode: {mode_lbl}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, hud_color, 2)
        cv2.putText(frame, "Neurix Gesture Cam | Q = quit",
                    (10, ch - 15), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (160, 160, 160), 1)

        cv2.imshow("Neurix Gesture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ══════════════════════════════════════════════════════════════════════
#  PANDA3D APPLICATION
# ══════════════════════════════════════════════════════════════════════
class ModularDesignApp(ShowBase):
    def __init__(self):
        super().__init__()

        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setBackgroundColor(0.15, 0.15, 0.18)
        self.disableMouse()

        self.camera.setPos(70, -140, 60)
        self.camera.lookAt(0, 0, 0)
        self.mouse_sensitivity = 0.2

        self.current_part    = None
        self.assembled_parts = []
        self.preview_models  = []

        self.setup_lights()
        self.create_grid(200)
        self.create_center_point()

        self.sub_menus = {}
        self.create_responsive_top_library()
        self.create_advanced_sidebar()
        self.create_gesture_hud()

        self.accept("enter",     self.finalize_part)
        self.accept("escape",    self.on_exit)
        self.accept("delete",    self.delete_current_part)
        self.accept("backspace", self.delete_current_part)

        self.camera_rot_active = False
        self.accept("mouse3",    self.set_camera_rot, [True])
        self.accept("mouse3-up", self.set_camera_rot, [False])

        self.taskMgr.add(self.update_task, "update_task")

        # ── Start gesture thread ────────────────────────────────
        t = threading.Thread(target=gesture_worker, daemon=True)
        t.start()

    # ── Gesture HUD (bottom center) ──────────────────────────────
    def create_gesture_hud(self):
        self.gesture_hud = OnscreenText(
            text="Gesture: OFF", pos=(0, -0.94),
            scale=0.05, fg=(0.3, 1, 0.6, 1),
            align=TextNode.ACenter, mayChange=True)

    def set_gesture_mode(self, mode):
        """Called from sidebar buttons — thread-safe mode switch."""
        with gs_lock:
            GS['mode']        = mode
            GS['prev_pinch']  = None
            GS['ctrl_active'] = False
            GS['grabbing']    = False
            # seed zoom from current part scale
            if mode == 'zoom' and self.current_part:
                GS['zoom_scale'] = self.current_part.getSx()

        lbl_map = {'rotate': 'ROTATE 🖐', 'move': 'MOVE ✋',
                   'zoom': 'ZOOM 🤏', None: 'OFF'}
        self.gesture_hud.setText(f"Gesture: {lbl_map.get(mode, 'OFF')}")

    # ── Grid + center ─────────────────────────────────────────────
    def create_center_point(self):
        OnscreenText(text='+', pos=(0,0), scale=0.08,
                     fg=(1,1,1,0.7), align=TextNode.ACenter)

    def create_grid(self, size):
        lines = LineSegs()
        for i in range(-size, size + 1, 5):
            lines.setThickness(1.0)
            lines.setColor(0.3, 0.3, 0.3, 0.2)
            lines.moveTo(i, -size, 0); lines.drawTo(i, size, 0)
            lines.moveTo(-size, i, 0); lines.drawTo(size, i, 0)
        self.render.attachNewNode(lines.create()).setTransparency(1)

    # ── Top shape library ─────────────────────────────────────────
    def create_responsive_top_library(self):
        self.top_panel = DirectFrame(
            frameColor=(0,0,0,0.8),
            frameSize=(-2.3, 2.3, -0.12, 0.12),
            parent=self.a2dTopCenter,
            pos=(0,0,-0.12), scale=0.6)

        shapes = [
            ("Moraaba","models/box",(1,0,0,1)),
            ("Mostateel","models/box",(0,1,0,1)),
            ("Dayra","models/misc/sphere",(0,0,1,1)),
            ("Mothalath","models/box",(1,1,0,1)),
            ("Kora","models/misc/sphere",(1,0,1,1)),
            ("Ostowana","models/box",(0,1,1,1)),
            ("Makhrut","models/misc/sphere",(1,0.5,0,1)),
            ("Haram","models/box",(0.5,0.5,0.5,1)),
            ("Najma","models/box",(1,1,1,1)),
            ("Khat","models/box",(1,1,1,1)),
            ("Sahm","models/box",(0,1,0,1)),
            ("Hexa","models/box",(0.3,0.3,0.3,1)),
            ("Oval","models/misc/sphere",(0.8,0.4,0.2,1)),
            ("Curve","models/box",(0.4,0.4,1,1)),
            ("Brush","models/box",(1,0.8,0.8,1)),
            ("Grid2D","models/box",(1,1,1,0.5)),
            ("GridSq","models/box",(1,1,1,0.3)),
            ("Nakes","models/misc/sphere",(0.5,0,0,1)),
        ]
        x_start = -2.1
        for i, (p_name, m_path, p_color) in enumerate(shapes):
            cont = self.top_panel.attachNewNode(f"cont_{p_name}")
            cont.setPos(x_start + i * 0.25, 0, 0)
            try:
                m = self.loader.loadModel(m_path)
                m.reparentTo(cont); m.setScale(0.015); m.setColor(p_color)
                self.preview_models.append(m)
                OnscreenText(text=p_name, pos=(0,-0.09), scale=0.04,
                             fg=(1,1,1,1), parent=cont)
            except: pass
            DirectButton(parent=cont, frameColor=(0,0,0,0),
                         frameSize=(-0.1,0.1,-0.1,0.1),
                         command=self.add_shape,
                         extraArgs=[p_name, m_path, p_color])

    # ── Sidebar ───────────────────────────────────────────────────
    def create_advanced_sidebar(self):
        self.side_bar = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.9),
            frameSize=(-0.12, 0.12, -1.15, 0.95),
            parent=self.a2dLeftCenter, pos=(0.12, 0, 0))

        # ── collapsible menus (بدون Gesture) ─────────────────────
        menu_data = [
            ("Add",    ["Fix Part", "Clear All"]),
            ("Select", ["Delete Part"]),
            ("Move",   ["Up (Z+)", "Down (Z-)", "Right (X+)", "Left (X-)"]),
            ("Rotate", ["Rot H+", "Rot P+", "Rot R+"]),
            ("Zoom",   ["In (+)", "Out (-)"]),
        ]
        y_pos = {
            "Add": 0.85, "Select": 0.65,
            "Move": 0.45, "Rotate": 0.05, "Zoom": -0.25,
        }
        for main_btn, subs in menu_data:
            cy = y_pos[main_btn]
            DirectButton(
                text=main_btn, scale=0.04, pos=(0,0,cy),
                parent=self.side_bar,
                frameColor=(0.3, 0.3, 0.3, 1), text_fg=(1,1,1,1),
                frameSize=(-2.2, 2.2, -0.6, 0.6),
                command=self.toggle_menu, extraArgs=[main_btn])
            sf = DirectFrame(parent=self.side_bar,
                             frameColor=(0,0,0,0), pos=(0,0,cy-0.1))
            self.sub_menus[main_btn] = sf
            sy = 0
            for opt in subs:
                DirectButton(
                    text=opt, scale=0.03, pos=(0.06,0,sy),
                    parent=sf, frameColor=(0.2,0.4,0.6,1),
                    text_fg=(1,1,1,1), frameSize=(-3.0,3.0,-0.5,0.5),
                    command=self.handle_action, extraArgs=[opt])
                sy -= 0.07
            sf.hide()

        # ── Gesture: أزرار دايماً ظاهرة ─────────────────────────
        OnscreenText(
            text="── Gesture ──", pos=(-0.095, -0.50),
            scale=0.038, fg=(0.3,1,0.6,1),
            parent=self.side_bar, align=TextNode.ALeft, mayChange=False)

        gesture_btns = [
            ("Rotate", "rotate", (0.18, 0.50, 0.28, 1)),
            ("Move",   "move",   (0.18, 0.28, 0.58, 1)),
            ("Zoom",   "zoom",   (0.52, 0.30, 0.10, 1)),
            ("Stop",   None,      (0.52, 0.10, 0.10, 1)),
        ]
        self.gesture_buttons = {}
        gy = -0.57
        for label, mode, color in gesture_btns:
            btn = DirectButton(
                text=label, scale=0.038, pos=(0,0,gy),
                parent=self.side_bar,
                frameColor=color, text_fg=(1,1,1,1),
                frameSize=(-2.5, 2.5, -0.6, 0.6),
                command=self.handle_gesture_btn, extraArgs=[mode])
            self.gesture_buttons[mode] = btn
            gy -= 0.085

    # ── Gesture button handler ────────────────────────────────────
    def handle_gesture_btn(self, mode):
        self.set_gesture_mode(mode)
        # visual feedback: الزرار النشط يتلون أبيض
        normal_colors = {
            "rotate": (0.18,0.50,0.28,1),
            "move":   (0.18,0.28,0.58,1),
            "zoom":   (0.52,0.30,0.10,1),
            None:      (0.52,0.10,0.10,1),
        }
        active_color = (0.9, 0.9, 0.2, 1)  # أصفر = نشط
        for m, btn in self.gesture_buttons.items():
            btn["frameColor"] = active_color if m == mode else normal_colors[m]

    # ── Shape builder ─────────────────────────────────────────────
    def add_shape(self, name, path, color):
        if self.current_part:
            self.finalize_part()
        self.current_part = self.loader.loadModel(path)
        self.current_part.reparentTo(self.render)
        self.current_part.setPos(0, 0, 5)
        self.current_part.setColor(color)

        scale_map = {
            "Moraaba":   (4, 4, 4),
            "Mostateel": (8, 2, 4),
            "Dayra":     (5, 5, 0.1),
            "Ostowana":  (1.5, 1.5, 8),
            "Khat":      (15, 0.1, 0.1),
        }
        if name in scale_map:
            self.current_part.setScale(*scale_map[name])
        elif name == "Mothalath":
            self.current_part.setScale(5, 0.1, 5)
            self.current_part.setShear((0, 25, 0))
        else:
            self.current_part.setScale(3)

        # seed zoom scale
        with gs_lock:
            GS['zoom_scale'] = self.current_part.getSx()

    # ── Sidebar toggle ────────────────────────────────────────────
    def toggle_menu(self, name):
        for k, f in self.sub_menus.items():
            if k == name:
                f.show() if f.isHidden() else f.hide()
            else:
                f.hide()

    # ── Keyboard / button actions ─────────────────────────────────
    def handle_action(self, action):
        p = self.current_part
        if not p and action != "Clear All":
            return
        actions = {
            "In (+)":     lambda: p.setScale(p.getScale() * 1.1),
            "Out (-)":    lambda: p.setScale(p.getScale() * 0.9),
            "Up (Z+)":    lambda: p.setZ(p.getZ() + 2),
            "Down (Z-)":  lambda: p.setZ(p.getZ() - 2),
            "Right (X+)": lambda: p.setX(p.getX() + 2),
            "Left (X-)":  lambda: p.setX(p.getX() - 2),
            "Rot H+":     lambda: p.setH(p.getH() + 22.5),
            "Delete Part":lambda: self.delete_current_part(),
            "Fix Part":   lambda: self.finalize_part(),
            "Clear All":  self._clear_all,
        }
        if action in actions:
            actions[action]()

    def _clear_all(self):
        for part in self.assembled_parts:
            part.removeNode()
        self.assembled_parts = []
        self.delete_current_part()

    # ── Main update task ──────────────────────────────────────────
    def update_task(self, task):
        dt = globalClock.getDt()

        # spin preview icons
        for m in self.preview_models:
            m.setH(m.getH() + 80 * dt)

        # right-drag camera rotation
        if self.camera_rot_active and self.mouseWatcherNode.hasMouse():
            md = self.win.getPointer(0)
            x, y   = md.getX(), md.getY()
            cx, cy = self.win.getXSize() // 2, self.win.getYSize() // 2
            self.camera.setH(self.camera.getH() - (x - cx) * self.mouse_sensitivity)
            self.camera.setP(self.camera.getP() - (y - cy) * self.mouse_sensitivity)
            self.win.movePointer(0, cx, cy)

        # ── Check fist_stop flag → update UI ─────────────────────
        with gs_lock:
            if GS.get('fist_stop'):
                GS['fist_stop'] = False
                self.gesture_hud.setText('Gesture: OFF')
                normal_colors = {
                    'rotate': (0.18,0.50,0.28,1),
                    'move':   (0.18,0.28,0.58,1),
                    'zoom':   (0.52,0.30,0.10,1),
                    None:     (0.52,0.10,0.10,1),
                }
                for m, btn in self.gesture_buttons.items():
                    btn['frameColor'] = normal_colors[m]

        # ── Apply gesture to current part ─────────────────────────
        if self.current_part:
            with gs_lock:
                mode = GS['mode']

                if mode == 'rotate' and GS['ctrl_active']:
                    # direct angle mapping (joystick style)
                    self.current_part.setH(GS['rot_y'])
                    self.current_part.setP(GS['rot_x'])

                elif mode == 'move' and GS['grabbing']:
                    # smooth lerp to pinch midpoint
                    cx = self.current_part.getX()
                    cz = self.current_part.getZ()
                    self.current_part.setX(cx + (GS['move_x'] - cx) * 0.15)
                    self.current_part.setZ(cz + (GS['move_z'] - cz) * 0.15)

                elif mode == 'zoom':
                    # smooth lerp to target scale
                    ts = GS['zoom_scale']
                    cs = self.current_part.getSx()
                    ns = cs + (ts - cs) * 0.12
                    self.current_part.setScale(ns)

        return task.cont

    # ── Lights ───────────────────────────────────────────────────
    def setup_lights(self):
        self.render.setLight(self.render.attachNewNode(AmbientLight("al")))
        dl   = DirectionalLight("dl")
        dlnp = self.render.attachNewNode(dl)
        dlnp.setHpr(45, -45, 0)
        self.render.setLight(dlnp)

    # ── Utils ─────────────────────────────────────────────────────
    def set_camera_rot(self, active):
        self.camera_rot_active = active
        props = WindowProperties()
        props.setCursorHidden(active)
        self.win.requestProperties(props)

    def delete_current_part(self, *_):
        if self.current_part:
            self.current_part.removeNode()
            self.current_part = None

    def finalize_part(self, *_):
        if self.current_part:
            self.current_part.setColor(self.current_part.getColor() * 0.9)
            self.assembled_parts.append(self.current_part)
            self.current_part = None

    def on_exit(self):
        stop_flag.set()
        import sys; sys.exit()


# ── Entry point ───────────────────────────────────────────────────────
app = ModularDesignApp()
try:
    app.run()
finally:
    stop_flag.set()
