from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenImage
from panda3d.core import (
    AmbientLight, DirectionalLight,
    loadPrcFileData, TextNode
)
import cv2
import mediapipe as mp

# إعدادات لضمان الجودة والظهور
loadPrcFileData("", "framebuffer-srgb true")
loadPrcFileData("", "textures-power-2 none")

class Viewer(ShowBase):
    def __init__(self):
        super().__init__()

        # 1. الخلفية والـ Sorting (عشان الموديل يفضل ظاهر)
        self.background = OnscreenImage(image='i-ron.jpeg', pos=(0, 0, 0), parent=self.render2d)#تحميل الخلفيه
        self.background.setBin('background', -100)#مهم بيخلي الخلفيه تبقي ورا اي حاجه
        self.background.setDepthWrite(False)
        self.cam.node().getDisplayRegion(0).setSort(20)#بيضمن ان الموديول يظهر

        # 2. الموديل (أيرون مان)
        self.pivot = self.render.attachNewNode("ironman_pivot")
        try:
            self.model = self.loader.loadModel("tonystark.glb")
            self.model.reparentTo(self.pivot)
            self.model.setHpr(0, 90, 0)
            
            # التوسيط بناءً على التجربة الناجحة
            b_min, b_max = self.model.getTightBounds()
            center = (b_min + b_max) / 2.0
            self.model.setPos(-center) 
            
            self.pivot.setScale(2.5) 
            self.pivot.setPos(0, 20, -3) 
            self.render.setShaderAuto()
        except:
            print("Model load error")

        # 3. الإضاءة
        alight = AmbientLight('alight')
        alight.setColor((0.8, 0.8, 0.8, 1))
        self.render.setLight(self.render.attachNewNode(alight))

        dlight = DirectionalLight('dlight')
        dlight.setColor((1.5, 1.5, 1.5, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setPos(0, -10, 10)
        dlnp.lookAt(self.pivot)
        self.render.setLight(dlnp)

        # 4. التحكم (Mouse & Modes)
        self.mode = "rotate" # الوضع الافتراضي
        self.setup_ui()
        self.setup_gestures()
        
        self.disableMouse()
        self.camera.setPos(0, 0, 0)
        self.camera.lookAt(self.pivot)
        
        # الماوس والتحريك
        self.dragging = False
        self.last_mpos = (0, 0)
        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)
        
        # إضافة المهام (Tasks)
        self.taskMgr.add(self.control_task, "control_task")

    def setup_ui(self):
        # العنوان
        OnscreenText(text="Your Hand-Your World", pos=(-1.1, 0.85), scale=0.06, fg=(0,1,1,1), align=TextNode.ALeft, parent=self.aspect2d)
        # فريم الزراير
        self.controls_frame = DirectFrame(frameColor=(0,0,0,0.4), pos=(0, 0, -0.85), frameSize=(-0.8, 0.8, -0.12, 0.12), parent=self.aspect2d)
        
        self.btn_rot = self.create_button("ROTATE", -0.5, lambda: self.set_mode("rotate"))
        self.btn_zoom = self.create_button("ZOOM", 0, lambda: self.set_mode("zoom"))
        self.btn_move = self.create_button("MOVE", 0.5, lambda: self.set_mode("move"))
        self.set_mode("rotate")

    def create_button(self, txt, x, cmd):
        return DirectButton(text=txt, scale=0.05, pos=(x, 0, -0.02), parent=self.controls_frame, 
                            command=cmd, frameSize=(-2, 2, -0.6, 0.8), text_scale=0.8)

    def set_mode(self, mode):
        self.mode = mode
        # تغيير الألوان للزراير عشان تعرف انت في أنهي وضع
        self.btn_rot["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "rotate" else (0.2, 0.2, 0.2, 1)
        self.btn_zoom["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "zoom" else (0.2, 0.2, 0.2, 1)
        self.btn_move["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "move" else (0.2, 0.2, 0.2, 1)

    def setup_gestures(self):
        self.cap = cv2.VideoCapture(0)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.dragging = True
            mpos = self.mouseWatcherNode.getMouse()
            self.last_mpos = (mpos.getX(), mpos.getY())

    def stop_drag(self): self.dragging = False

    def control_task(self, task):
        # 1. الماوس
        if self.dragging and self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            dx = mpos.getX() - self.last_mpos[0]
            dy = mpos.getY() - self.last_mpos[1]
            
            if self.mode == "rotate":
                self.pivot.setH(self.pivot.getH() - dx * 100)
                self.pivot.setP(self.pivot.getP() + dy * 100)
            elif self.mode == "zoom":
                self.pivot.setY(self.pivot.getY() + dy * 20)
            elif self.mode == "move":
                self.pivot.setX(self.pivot.getX() + dx * 15)
                self.pivot.setZ(self.pivot.getZ() + dy * 15)
            
            self.last_mpos = (mpos.getX(), mpos.getY())

        # 2. الـ Gestures
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0].landmark
                # مثال: تحريك الموديل يمين وشمال مع حركة كف الإيد
                self.pivot.setH(self.pivot.getH() + (lm[0].x - 0.5) * 5)
            
            cv2.imshow("Stark HUD", frame)
            cv2.waitKey(1)

        return task.cont

if __name__ == "__main__":
    app = Viewer()
    app.run()