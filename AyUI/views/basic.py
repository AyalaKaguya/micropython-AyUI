from AyUI import View
from AyUI import Drawable

class BasicView(View):
    """基本视图，任何布局交由子元素管理"""

    def __init__(self, *elements,
                 space=(0, 0),
                 margin=(0, 0, 0, 0),   # 外边距 左上右下
                 padding=(0, 0, 0, 0),  # 内边距 左上右下
                 border=0,              # 边框宽度
                 border_color=1):       # 边框颜色
        self.elements = list(elements)
        self.space = space
        self.margin = margin
        self.padding = padding
        self.border = border
        self.border_color = border_color
        self.spaces = []

    @property
    def _edge_h(self):
        return self.margin[1] + self.margin[3] + self.border

    @property
    def _edge_w(self):
        return self.margin[0] + self.margin[2] + self.border

    def draw(self, framebuf, axis=(0, 0)):
        # margin
        ele_axis = [axis[0]+self.margin[0], axis[1]+self.margin[1]]
        
        # border
        for b in range(self.border):
            framebuf.rect(
                ele_axis[0]+b,
                ele_axis[1]+b,
                self.space[0]+2*(self.border-b),
                self.space[1]+2*(self.border-b),
                self.border_color)
        
        # padding
        ele_axis=[
            ele_axis[0]+self.border+self.padding[0],
            ele_axis[1]+self.border+self.padding[1]
        ]
        
        # elements
        for ele in self.elements:
            ele.draw(framebuf, tuple(ele_axis))

    def calc(self, f_space=(0, 0)):
        return (self.space[0]+self._edge_w,self.space[1]+self._edge_h)