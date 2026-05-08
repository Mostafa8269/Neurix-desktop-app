# Main.py
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
import numpy as np
import pyautogui
import time
import os

# --- استيراد الموديولات الجديدة ---
from hologram_ui import HologramUI
from interaction import InteractionManager

# اعدادات الجودة
loadPrcFileData("", "framebuffer-srgb true")
loadPrcFileData("", "textures-power-2 none")

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0 
SCREEN_W, SCREEN_H = pyautogui.size()

class Viewer(ShowBase):
    def __init__(self):
        super().__init__()

        # 1. تحميل ملفات الصوت وتحضيرها
        self.intro_voice = self.loader.loadSfx("intro_voice.mp3")
        self.helmet_voice = self.loader.loadSfx("helmet.mp3")
        self.arcreactor_voice = self.loader.loadSfx("arcreactor.mp3")
        self.repulsors_voice = self.loader.loadSfx("repulsors.mp3")
        self.thrusters_voice = self.loader.loadSfx("flightthrusters.mp3") # تحميل صوت المحركات
        
        self.voice_played = False # لضمان تشغيل صوت البداية مرة واحدة فقط

        # --- إعدادات الأداء ---
        self.SENSITIVITY = 1.2   
        self.SMOOTH = 0.3        
        self.DEAD_ZONE = 5       
        self.COOLDOWN = 0.3      
        self.CLICK_THRESHOLD = 0.04 
        
        self.last_click_time = 0
        self.smooth_x = SCREEN_W // 2
        self.smooth_y = SCREEN_H // 2
        self.prev_sx = SCREEN_W // 2
        self.prev_sy = SCREEN_H // 2

        # 1. الخلفية
        try:
            self.background = OnscreenImage(image='plainbackground.jpeg', pos=(0, 0, 0), parent=self.render2d)
            self.background.setBin('background', -100)
            self.background.setDepthWrite(False)
        except:
            print("Warning: Background image 'plainbackground.jpeg' not found.")
        
        self.cam.node().getDisplayRegion(0).setSort(20)

        # 2. الموديل
        self.pivot = self.render.attachNewNode("ironman_pivot")
        try:
            self.model = self.loader.loadModel("tonystark.glb")
            self.model.reparentTo(self.pivot)
            self.model.setColorScale(4.0, 4.0, 4.0, 1.0)
            self.model.setHpr(0, 0, 0) 
            b_min, b_max = self.model.getTightBounds()
            self.model.setPos(-(b_min[0] + b_max[0])/2, -(b_min[1] + b_max[1])/2, -b_min[2])
            self.pivot.setScale(2.5)
            self.pivot.setPos(0, 20, -2.5) 
            self.render.setShaderAuto()
        except:
            pass

        # 3. الاضاءة
        alight = AmbientLight('alight')
        alight.setColor((1.8, 1.8, 1.8, 1))
        self.render.setLight(self.render.attachNewNode(alight))
        
        dlight = DirectionalLight('dlight')
        dlight.setColor((2.5, 2.5, 2.5, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setPos(0, -15, 15)
        dlnp.lookAt(self.pivot)
        self.render.setLight(dlnp)

        # 4. التحكم والواجهة
        self.mode = "rotate"
        self.setup_ui()
        
        self.hologram_sys = HologramUI(self.aspect2d)
        self.interact_sys = InteractionManager(self, self.model, self.hologram_sys)
        
        self.setup_gestures()
        self.disableMouse()
        self.camera.setPos(0, 0, 0)
        self.camera.lookAt(self.pivot)

        self.dragging = False
        self.last_mpos = (0, 0)
        self.accept("mouse1", self.start_drag)
        self.accept("mouse1-up", self.stop_drag)

        self.last_pinch_dist = 0
        self.taskMgr.add(self.control_task, "control_task")

    def setup_ui(self):
        OnscreenText(text="STARK OS - EXCLUSIVE MODE", pos=(-1.2, 0.85), scale=0.06, 
                    fg=(0,1,1,1), align=TextNode.ALeft, parent=self.aspect2d)
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
        self.last_pinch_dist = 0 
        self.btn_rot["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "rotate" else (0.2, 0.2, 0.2, 1)
        self.btn_zoom["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "zoom" else (0.2, 0.2, 0.2, 1)
        self.btn_move["frameColor"] = (0.9, 0.5, 0.1, 1) if mode == "move" else (0.2, 0.2, 0.2, 1)

    def setup_gestures(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.8, 
                                         min_tracking_confidence=0.8)
        self.mp_draw = mp.solutions.drawing_utils

    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.interact_sys.process_selection()
            self.dragging = True
            mpos = self.mouseWatcherNode.getMouse()
            self.last_mpos = (mpos.getX(), mpos.getY())

    def stop_drag(self):
        self.dragging = False

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
            if not self.voice_played:
                if self.intro_voice:
                    self.intro_voice.play()
                self.voice_played = True 

            frame = cv2.flip(frame, 1)
            display = frame.copy()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            gesture_text = "IDLE"
            gesture_color = (128, 128, 128)

            if results.multi_hand_landmarks:
                hand_lms = results.multi_hand_landmarks[0]
                lms = hand_lms.landmark
                self.mp_draw.draw_landmarks(display, hand_lms, self.mp_hands.HAND_CONNECTIONS)

                idx_tip = lms[8]
                sx = int(((idx_tip.x * SCREEN_W) * self.SENSITIVITY))
                sy = int(((idx_tip.y * SCREEN_H) * self.SENSITIVITY))
                sx = max(0, min(SCREEN_W, sx))
                sy = max(0, min(SCREEN_H, sy))
                nx = sx if abs(sx - self.prev_sx) > self.DEAD_ZONE else self.prev_sx
                ny = sy if abs(sy - self.prev_sy) > self.DEAD_ZONE else self.prev_sy
                self.smooth_x = self.smooth_x + self.SMOOTH * (nx - self.smooth_x)
                self.smooth_y = self.smooth_y + self.SMOOTH * (ny - self.smooth_y)
                self.prev_sx, self.prev_sy = int(self.smooth_x), int(self.smooth_y)
                pyautogui.moveTo(int(self.smooth_x), int(self.smooth_y), duration=0)

                pinch_dist = math.hypot(lms[8].x - lms[4].x, lms[8].y - lms[4].y)
                if pinch_dist < self.CLICK_THRESHOLD:
                    gesture_text = "SYSTEM CLICK!"
                    gesture_color = (0, 255, 0)
                    current_time = time.time()
                    if current_time - self.last_click_time > self.COOLDOWN:
                        pyautogui.click()
                        self.last_click_time = current_time

                index_tip = lms[8]
                index_up = index_tip.y < lms[6].y
                middle_up = lms[12].y < lms[10].y
                ring_up = lms[16].y < lms[14].y
                pinky_up = lms[20].y < lms[18].y

                if self.mode == "rotate":
                    if index_up and not middle_up and not ring_up and not pinky_up:
                        gesture_text = "ROTATING"
                        gesture_color = (0, 255, 255)
                        target_h = (index_tip.x - 0.5) * 180
                        target_p = (index_tip.y - 0.5) * -180
                        self.pivot.setH(self.pivot.getH() + (target_h - self.pivot.getH()) * 0.1)
                        self.pivot.setP(self.pivot.getP() + (target_p - self.pivot.getP()) * 0.1)

                elif self.mode == "zoom":
                    if index_up:
                        gesture_text = "ZOOMING"
                        gesture_color = (0, 255, 0)
                        if self.last_pinch_dist > 0:
                            delta = pinch_dist - self.last_pinch_dist
                            self.pivot.setY(self.pivot.getY() - delta * 300)
                            self.pivot.setY(max(5, min(100, self.pivot.getY())))
                        self.last_pinch_dist = pinch_dist

                elif self.mode == "move":
                    if index_up and middle_up:
                        gesture_text = "MOVING"
                        gesture_color = (255, 100, 0)
                        palm_center = ((lms[0].x + lms[9].x)/2, (lms[0].y + lms[9].y)/2)
                        target_x = (palm_center[0] - 0.5) * 40 
                        target_z = (0.5 - palm_center[1]) * 30
                        self.pivot.setX(self.pivot.getX() + (target_x - self.pivot.getX()) * 0.3)
                        self.pivot.setZ(self.pivot.getZ() + (target_z - self.pivot.getZ()) * 0.3)
                else:
                    self.last_pinch_dist = 0
            else:
                self.last_pinch_dist = 0

            cv2.rectangle(display, (10, 10), (450, 150), (0, 0, 0), -1)
            cv2.putText(display, "STARK OS - SYSTEM CONTROL", (20, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            cv2.putText(display, "MODE: " + self.mode.upper(), (20, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(display, "GESTURE: " + gesture_text, (20, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, gesture_color, 2)

            cv2.imshow("Stark HUD - System Control", display)
            cv2.waitKey(1)

        return task.cont

    def destroy(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        cv2.destroyAllWindows()
        super().destroy()

if __name__ == "__main__":
    app = Viewer()
    try:
        app.run()
    except SystemExit:
        app.destroy()