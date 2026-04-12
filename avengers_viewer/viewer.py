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
