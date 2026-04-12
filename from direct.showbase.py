from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight

class Viewer(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()

        # تحميل المجسم
        self.model = self.loader.loadModel("avenger.glb")
        self.model.reparentTo(self.render)

        # 🧠 إصلاح الاتجاه + التمركز
        self.model.setScale(1)
        self.model.setPos(0, 0, 0)

        # 🔥 Fix rotation (نايم على جنبه)
        self.model.setH(90)
        self.model.setP(90)
        self.model.setR(180)

        # 📸 الكاميرا (بعيدة ومظبوطة)
        self.camera.setPos(0, -400, 40)
        self.camera.lookAt(0, 0, 90)

        # 💡 إضاءة قوية عشان المجسم الأبيض يبان
        dlight = DirectionalLight('dlight')
        dlight.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor((0.6, 0.6, 0.6, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # 🔄 دوران بسيط للتأكد إنه شغال
        self.taskMgr.add(self.rotate, "rotate")

    def rotate(self, task):
        self.model.setH(self.model.getH() + 0.3)
        return task.cont


app = Viewer()
app.run()












import pygame
import numpy as np
from panda3d.core import loadPrcFileData
from direct.showbase.ShowBase import ShowBase
from panda3d.core import FrameBufferProperties, WindowProperties
import sys
import threading

# ======================
# PYGAME UI
# ======================
pygame.init()

W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("3D Embedded UI")

BLACK = (0,0,0)
GRAY = (40,40,40)
WHITE = (255,255,255)

# ======================
# PAND3D OFFSCREEN
# ======================
loadPrcFileData("", "window-type offscreen")

class Renderer(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.model = self.loader.loadModel("avenger.glb")
        self.model.reparentTo(self.render)
        self.model.setScale(2)

        self.distance = 20

    def render_frame(self):
        self.taskMgr.step()
        tex = self.win.getScreenshot()
        return tex

renderer = Renderer()

# ======================
# UI LOOP
# ======================
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # UI BACKGROUND
    screen.fill(BLACK)

    # UI PANEL
    pygame.draw.rect(screen, GRAY, (50, 50, 300, 600), border_radius=20)

    # 3D VIEWPORT BOX
    pygame.draw.rect(screen, (20,20,20), (400, 50, 800, 600), border_radius=20)

    # render 3D frame
    tex = renderer.win.getScreenshot()

    if tex:
        data = tex.getRamImageAs("RGBA")
        img = pygame.image.fromstring(data.getData(), (tex.getXSize(), tex.getYSize()), "RGBA")
        img = pygame.transform.scale(img, (800, 600))
        screen.blit(img, (400, 50))

    pygame.display.flip()
    clock.tick(30)