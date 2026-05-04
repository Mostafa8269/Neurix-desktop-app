from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectButton, DirectFrame, OnscreenImage
from panda3d.core import (
    AmbientLight, DirectionalLight,
    loadPrcFileData, TextNode
)
import cv2
import mediapipe as mp
import math

# اعدادات لضمان الجودة والظهور
loadPrcFileData("", "framebuffer-srgb true")
loadPrcFileData("", "textures-power-2 none")

class Viewer(ShowBase):
    def __init__(self):
        super().__init__()

        # 1. الخلفية والـ Sorting (عشان الموديل يفضل ظاهر)
        self.background = OnscreenImage(image='i-ron.jpeg', pos=(0, 0, 0), parent=self.render2d)
        self.background.setBin('background', -100)
        self.background.setDepthWrite(False)
        self.cam.node().getDisplayRegion(0).setSort(20)

        # 2. الموديل (ايرون مان)
        self.pivot = self.render.attachNewNode("ironman_pivot")
        try:
            self.model = self.loader.loadModel("tonystark.glb")
            self.model.reparentTo(self.pivot)
            self.model.setHpr(0, 90, 0)

            b_min, b_max = self.model.getTightBounds()
            center = (b_min + b_max) / 2.0
            self.model.setPos(-center)

            self.pivot.setScale(2.5)
            self.pivot.setPos(0, 20, -3)
            self.render.setShaderAuto()
        except:
            print("Model load error - using fallback cube")
            from panda3d.core import GeomVertexFormat, GeomVertexData
            from panda3d.core import Geom, GeomTriangles, GeomVertexWriter
            from panda3d.core import GeomNode

            format = GeomVertexFormat.getV3n3c4()
            vdata = GeomVertexData('cube', format, Geom.UHStatic)
            vertex = GeomVertexWriter(vdata, 'vertex')
            normal = GeomVertexWriter(vdata, 'normal')
            color = GeomVertexWriter(vdata, 'color')

            for x, y, z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]:
                vertex.addData3(x, y, z)
                normal.addData3(0, 0, 1)
                color.addData4f(0.8, 0.1, 0.1, 1)

            prim = GeomTriangles(Geom.UHStatic)
            for f in [(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,5,1),(0,4,5),(2,6,7),(2,1,6),(0,7,4),(0,3,7),(1,5,6),(1,6,2)]:
                prim.addVertices(*f)

            geom = Geom(vdata)
            geom.addPrimitive(prim)
            node = GeomNode('cube')
            node.addGeom(geom)
            self.model = self.pivot.attachNewNode(node)
            self.model.setScale(2)

        # 3. الاضاءة
        alight = AmbientLight('alight')
        alight.setColor((0.8, 0.8, 0.8, 1))
        self.render.setLight(self.render.attachNewNode(alight))

        dlight = DirectionalLight('dlight')
        dlight.setColor((1.5, 1.5, 1.5, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setPos(0, -10, 10)
        dlnp.lookAt(self.pivot)
        self.render.setLight(dlnp)

        # 4. التحكم (Mouse & Gestures)
        self.mode = "rotate"
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

        # متغيرات الجيستشر
        self.gesture_active = False
        self.gesture_mode = "none"
        self.last_pinch_dist = 0
        self.grab_offset = (0, 0)

        # اضافة المهام (Tasks)
        self.taskMgr.add(self.control_task, "control_task")

    def setup_ui(self):
        # العنوان
        OnscreenText(text="Your Hand-Your World", pos=(-1.5, 0.85), scale=0.06, 
                    fg=(0,1,1,1), align=TextNode.ALeft, parent=self.aspect2d)
        OnscreenText(text="", pos=(-1.1, 0.75), scale=0.04, 
                    fg=(1,1,0,1), align=TextNode.ALeft, parent=self.aspect2d)

        # فريم الزراير
        self.controls_frame = DirectFrame(frameColor=(0,0,0,0.4), pos=(0, 0, -0.85), 
                                         frameSize=(-0.8, 0.8, -0.12, 0.12), parent=self.aspect2d)

        self.btn_rot = self.create_button("ROTATE", -0.5, lambda: self.set_mode("rotate"))
        self.btn_zoom = self.create_button("ZOOM", 0, lambda: self.set_mode("zoom"))
        self.btn_move = self.create_button("MOVE", 0.5, lambda: self.set_mode("move"))
        self.set_mode("rotate")

    def create_button(self, txt, x, cmd):
        return DirectButton(text=txt, scale=0.05, pos=(x, 0, -0.02), parent=self.controls_frame, 
                           command=cmd, frameSize=(-2, 2, -0.6, 0.8), text_scale=0.8)

    def set_mode(self, mode):
        self.mode = mode
        self.btn_rot["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "rotate" else (0.2, 0.2, 0.2, 1)
        self.btn_zoom["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "zoom" else (0.2, 0.2, 0.2, 1)
        self.btn_move["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "move" else (0.2, 0.2, 0.2, 1)

    def setup_gestures(self):
        self.cap = cv2.VideoCapture(0)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, 
                                         min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.dragging = True
            mpos = self.mouseWatcherNode.getMouse()
            self.last_mpos = (mpos.getX(), mpos.getY())

    def stop_drag(self):
        self.dragging = False

    def detect_gesture(self, lms):
        thumb_tip = lms[4]
        index_tip = lms[8]
        index_pip = lms[6]
        middle_tip = lms[12]
        middle_pip = lms[10]
        ring_tip = lms[16]
        ring_pip = lms[14]
        pinky_tip = lms[20]
        pinky_pip = lms[18]

        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y

        pinch_dist = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)

        if pinch_dist < 0.08:
            return "zoom", {"dist": pinch_dist, "center": ((thumb_tip.x + index_tip.x)/2, 
                                                          (thumb_tip.y + index_tip.y)/2)}

        if index_up and not middle_up and not ring_up and not pinky_up:
            return "rotate", {"x": index_tip.x, "y": index_tip.y}

        if index_up and middle_up and ring_up and pinky_up:
            palm_center = ((lms[0].x + lms[9].x)/2, (lms[0].y + lms[9].y)/2)
            return "move", {"x": palm_center[0], "y": palm_center[1]}

        return "none", {}

    def control_task(self, task):
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

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            display = frame.copy()

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            gesture_text = "No Hand"
            gesture_color = (128, 128, 128)

            if results.multi_hand_landmarks:
                hand_lms = results.multi_hand_landmarks[0]
                lms = hand_lms.landmark

                self.mp_draw.draw_landmarks(display, hand_lms, self.mp_hands.HAND_CONNECTIONS)

                gesture, data = self.detect_gesture(lms)

                if gesture == "rotate":
                    gesture_text = "ROTATE"
                    gesture_color = (0, 255, 255)

                    angle_y = (data["x"] - 0.5) * 360
                    angle_x = (data["y"] - 0.5) * -360

                    current_h = self.pivot.getH()
                    current_p = self.pivot.getP()

                    self.pivot.setH(current_h + (angle_y - current_h) * 0.1)
                    self.pivot.setP(current_p + (angle_x - current_p) * 0.1)

                elif gesture == "zoom":
                    gesture_text = "ZOOM"
                    gesture_color = (0, 255, 0)

                    curr_dist = data["dist"]

                    if self.last_pinch_dist > 0:
                        delta = curr_dist - self.last_pinch_dist
                        new_y = self.pivot.getY() - delta * 200
                        new_y = max(5, min(100, new_y))
                        self.pivot.setY(new_y)

                    self.last_pinch_dist = curr_dist

                    thumb_tip = lms[4]
                    index_tip = lms[8]
                    t_x, t_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
                    i_x, i_y = int(index_tip.x * w), int(index_tip.y * h)
                    cv2.line(display, (t_x, t_y), (i_x, i_y), (0, 255, 0), 3)

                elif gesture == "move":
                    gesture_text = "MOVE"
                    gesture_color = (255, 100, 0)

                    target_x = (data["x"] - 0.5) * 20
                    target_z = (0.5 - data["y"]) * 15

                    current_x = self.pivot.getX()
                    current_z = self.pivot.getZ()

                    self.pivot.setX(current_x + (target_x - current_x) * 0.15)
                    self.pivot.setZ(current_z + (target_z - current_z) * 0.15)

                    self.last_pinch_dist = 0

                else:
                    gesture_text = "IDLE"
                    gesture_color = (200, 200, 200)
                    self.last_pinch_dist = 0
            else:
                self.last_pinch_dist = 0

            overlay = display.copy()
            cv2.rectangle(overlay, (10, 10), (450, 140), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, display, 0.4, 0, display)

            cv2.putText(display, "STARK INDUSTRIES - HAND CONTROL", (20, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            cv2.putText(display, "MODE: " + self.mode.upper(), (20, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(display, "GESTURE: " + gesture_text, (20, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, gesture_color, 2)

            pos_text = "Pos: ({:.1f}, {:.1f}, {:.1f})".format(self.pivot.getX(), self.pivot.getY(), self.pivot.getZ())
            cv2.putText(display, pos_text, (20, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

            cv2.imshow("Stark HUD - Hand Control", display)
            cv2.waitKey(1)

        return task.cont

    def destroy(self):
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy()

if __name__ == "__main__":
    app = Viewer()
    try:
        app.run()
    except SystemExit:
        app.destroy()
