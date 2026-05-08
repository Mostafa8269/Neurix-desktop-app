# hologram_ui.py
from direct.gui.DirectGui import DirectFrame, OnscreenText
from panda3d.core import TextNode

class HologramUI:
    def __init__(self, parent):
        # تم تغيير pos ليكون بالسالب (-1.2) عشان يروح أقصى الشمال
        # وتغيير frameSize عشان يبدأ الرسم من الشمال لليمين بشكل متناسق
        self.panel = DirectFrame(
            frameColor=(0, 0.1, 0.2, 0.4), 
            frameSize=(0, 0.75, -0.05, 0.6), 
            pos=(-1.25, 0, 0.1), # القيمة دي هي اللي نقلته للشمال             
            parent=parent,
            borderWidth=(0.01, 0.01)
        )
        
        # العنوان
        self.title_text = OnscreenText(
            text="", 
            parent=self.panel, 
            scale=0.075, 
            pos=(0.05, 0.48), 
            fg=(0, 1, 1, 1), 
            shadow=(0, 0, 0, 1), 
            shadowOffset=(0.06, 0.06), 
            align=TextNode.ALeft, 
            mayChange=True
        )

        # النص التفصيلي
        self.desc_text = OnscreenText(
            text="", 
            parent=self.panel, 
            scale=0.045, 
            pos=(0.05, 0.35), 
            fg=(0.95, 0.95, 0.95, 1), 
            shadow=(0, 0, 0, 0.9), 
            shadowOffset=(0.04, 0.04),
            align=TextNode.ALeft, 
            wordwrap=15, 
            mayChange=True
        )
        
        self.panel.hide()

    def show_info(self, title, desc, pos=None):
        self.title_text.setText(str(title).upper())
        self.desc_text.setText(str(desc))
        self.panel.show()

    def hide_info(self):
        self.panel.hide()

    def display(self, data, x_click=0, y_click=0):
        if isinstance(data, dict):
            self.show_info(data.get("title"), data.get("desc"))

    def hide(self):
        self.hide_info()