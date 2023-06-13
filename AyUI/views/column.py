from AyUI import View,Drawable
from AyUI.views.basic import BasicView

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