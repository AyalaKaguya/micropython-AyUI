from ayui import View,Drawable

class BasicView(View):
    """基本视图，任何布局交由子元素管理"""

    def __init__(self, *elements,
                 # 宽高 0:未定义 -1:计算值 -2:最大值 <-2:跟随父值 >0:定义值
                 space=(0, 0),
                 margin=(0, 0, 0, 0),   # 外边距 左上右下
                 padding=(0, 0, 0, 0),  # 内边距 左上右下
                 border=0,              # 边框宽度
                 border_color=1):  # 边框颜色
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

class ColumnView(BasicView):
    """列视图，从上往下"""
    
    def draw(self, framebuf, axis=(0, 0)):
        # TODO 列视图绘制
        pass
    
    def calc(self, f_space=(0, 0)):
        # RowView 宽度计算子元素最宽宽度，高度通过计算得到
        # ColumnView 宽度通过计算得出，高度计算子元素最高高度
        # 传入可用空间，传出占用空间
        l_space = [f_space[0]-self._edge_w, f_space[1]-self._edge_h] # 剩余空间
        space= [self._edge_w, self._edge_h] # 占用空间

        for i in self.elements:
            if isinstance(i, View):
                (w, h) = i.calc(f_space=tuple(l_space)) # 传入该元素剩余空间
                self.spaces.append((w, h))          # 元素 -> 空间对应表
                l_space = [l_space[0],l_space[1]-h] # 列视图剩余空间只减去高
                space = [space[0], space[1]+h]      # 列视图占用空间只加上高
            elif isinstance(i, Drawable):
                w, h = i.width, i.height
                self.spaces.append((w, h))
                l_space = [l_space[0],l_space[1]-h]
                space = [space[0], space[1]+h]
            else:
                print(
                    "[WARN] Unexpected elements appear, which can lead to calculation errors.")
                
        return tuple(space)