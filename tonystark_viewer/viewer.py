from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, DirectionalLight, loadPrcFileData

# خاص بالألوان
loadPrcFileData("", "framebuffer-srgb true")

class Viewer(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()

        # الموديل بتاع عمو توني ستارك
        self.pivot = self.render.attachNewNode("pivot_node")
        self.model = self.loader.loadModel("tonystark.glb")
        self.model.reparentTo(self.pivot)

        # البوزيشن بتاع الراجل اللي داخ من كتر اللف
        self.model.setHpr(0, 90, 0) 
        self.model.setPos(0, 0, 0)
        bounds = self.model.getTightBounds()
        center = (bounds[0] + bounds[1]) * 0.5
        self.model.setPos(-center)

        self.camera.setPos(0, -10, 0)
        self.camera.lookAt(self.pivot)

        # ==== ظبط الاضاءه عشان تكون مشعه =====
        
        # 1.
        dlight = DirectionalLight('dlight')
        dlight.setColor((3.0, 3.0, 3.0, 1)) # أئي قيمه اعلي من واحد هتدينا شعاع ها
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0)
        self.render.setLight(dlnp)

        # 2.  عشان ميبقاش فيه سواد في الضل
        alight = AmbientLight('alight')
        alight.setColor((1.5, 1.5, 1.5, 1)) # تنوير شامل للمجسم
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)

        # هنا عشان نخلي البدلة بتلمع
        self.render.setShaderAuto()

        self.taskMgr.add(self.rotate_model_task, "rotate_model_task")

    def rotate_model_task(self, task):
        self.pivot.setH(self.pivot.getH() + 0.3)
        return task.cont

app = Viewer()
app.run()