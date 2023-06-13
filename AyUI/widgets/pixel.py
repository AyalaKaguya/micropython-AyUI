from AyUI import Drawable

class Pixel(Drawable):
    """基本绘画元素, 一个点"""

    def __init__(self, 
                 color,
                 axis=(0, 0),           # 相对绘图原点
                 margin=(0, 0, 0, 0),   # 外边距 左上右下
                 padding=(0, 0, 0, 0),  # 内边距 左上右下
                 border=0,              # 边框
                 border_color=1):       # 边框颜色
        self.axis = axis
        self.margin = margin
        self.padding = padding
        self.border = border
        self.border_color = border_color
        self.color = color

    @property
    def width(self):
        return 1 + \
            self.margin[0] + self.margin[2] + self.border + self.padding[0] + self.padding[2]

    @property
    def height(self):
        return 1 + \
            self.margin[1] + self.margin[3] + self.border + self.padding[1] + self.padding[3]

    def draw(self, framebuf, axis):
        # margin
        ele_axis = [axis[0]+self.margin[0], axis[1]+self.margin[1]] # 左上绘图原点
        
        # border
        for b in range(self.border):
            framebuf.rect(
                ele_axis[0]+b,
                ele_axis[1]+b,
                1+self.padding[0]+self.padding[2]+2*(self.border-b),
                1+self.padding[1]+self.padding[3]+2*(self.border-b),
                self.border_color)
        
        # padding
        ele_axis=[
            ele_axis[0]+self.border+self.padding[0],
            ele_axis[1]+self.border+self.padding[1]
        ]
        
        framebuf.pixel(ele_axis[0], ele_axis[1], self.color)