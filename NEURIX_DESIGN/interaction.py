# interaction.py
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerQueue, CollisionRay, BitMask32
from info_data import PARTS_INFO

class InteractionManager:
    def __init__(self, base, model, ui):
        self.base = base
        self.model = model
        self.ui = ui

        self.picker = CollisionTraverser()
        self.handler = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = self.base.camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.model.setCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.handler)

    # دالة لإيقاف جميع الأصوات الحالية
    def stop_all_voices(self):
        voices = ['helmet_voice', 'arcreactor_voice', 'repulsors_voice', 'thrusters_voice']
        for v in voices:
            voice_obj = getattr(self.base, v, None)
            if voice_obj:
                voice_obj.stop()

    def process_selection(self):
        if self.base.mouseWatcherNode.hasMouse():
            mpos = self.base.mouseWatcherNode.getMouse()
            mouse_x = mpos.getX()
            mouse_y = mpos.getY()
            
            self.pickerRay.setFromLens(self.base.camNode, mouse_x, mouse_y)
            self.picker.traverse(self.base.render)

            if self.handler.getNumEntries() > 0:
                self.handler.sortEntries()
                entry = self.handler.getEntry(0)
                hit_pos = entry.getSurfacePoint(self.model)
                z = hit_pos.getZ()
                x = hit_pos.getX()
                
                print(f"Targeting: Z={z:.2f}, X={x:.2f}")

                selected_part = None
                
                if z > 3.3: 
                    selected_part = PARTS_INFO["HELMET"]
                    # إيقاف أي صوت شغال وتشغيل صوت الخوذة
                    self.stop_all_voices()
                    if hasattr(self.base, 'helmet_voice'):
                        self.base.helmet_voice.play()
                elif 2.6 < z <= 3.3:
                    selected_part = PARTS_INFO["ARC_REACTOR"]
                    # إيقاف أي صوت شغال وتشغيل صوت المفاعل
                    self.stop_all_voices()
                    if hasattr(self.base, 'arcreactor_voice'):
                        self.base.arcreactor_voice.play()
                elif 1.5 < z <= 2.6:
                    if abs(x) > 0.4:
                        selected_part = PARTS_INFO["HANDS"]
                        # إيقاف أي صوت شغال وتشغيل صوت الـ Repulsors
                        self.stop_all_voices()
                        if hasattr(self.base, 'repulsors_voice'):
                            self.base.repulsors_voice.play()
                    else:
                        selected_part = PARTS_INFO["ARC_REACTOR"]
                        # إيقاف أي صوت شغال وتشغيل صوت المفاعل
                        self.stop_all_voices()
                        if hasattr(self.base, 'arcreactor_voice'):
                            self.base.arcreactor_voice.play()
                elif z <= 1.5:
                    selected_part = PARTS_INFO["LEGS"]
                    # إيقاف أي صوت شغال وتشغيل صوت المحركات
                    self.stop_all_voices()
                    if hasattr(self.base, 'thrusters_voice'):
                        self.base.thrusters_voice.play()

                if selected_part:
                    self.ui.display(selected_part, mouse_x, mouse_y)
            else:
                self.ui.hide()