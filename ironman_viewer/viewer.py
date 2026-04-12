from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight

class Viewer(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()

        # محاولة تحميل الموديل
        try:
            self.model = self.loader.loadModel("ironman.glb")
            print("✅ Model loaded")
        except:
            print("❌ Model failed to load")
            return

        # إضافة الموديل
        self.model.reparentTo(self.render)

        # 👇 نخليه واضح مهما كان حجمه
        self.model.setScale(20)
        self.model.setPos(0, 50, 0)

        # إضاءة قوية
        dlight = DirectionalLight('dlight')
        dlight.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        alight = AmbientLight('alight')
        alight.setColor((0.8, 0.8, 0.8, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # كاميرا بعيدة شوية عشان تشوف أي حاجة
        self.camera.setPos(0, -200, 80)
        self.camera.lookAt(0, 0, 0)

        # دوران عشان تتأكد إنه ظاهر
        self.taskMgr.add(self.rotate, "rotate")

    def rotate(self, task):
        self.model.setH(self.model.getH() + 0.5)
        return task.cont

app = Viewer()
app.run()