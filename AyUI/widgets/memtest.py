from AyUI import Drawable
import gc


class Memtest(Drawable):
    """内存测试组件"""

    def __init__(self, color=0):
        self.color = color

    @property
    def width(self):
        return 120

    @property
    def height(self):
        return 30

    def draw(self, framebuf, axis):
        mem_free, mem_alloc = gc.mem_free(), gc.mem_alloc()
        mem_total = mem_free + mem_alloc
        framebuf.text("mem: %d %%" %
                      (int(mem_alloc*100/mem_total)), axis[0]+2, axis[1]+2, self.color)
        framebuf.text("%d/%d" %
                      (mem_alloc, mem_total), axis[0]+2, axis[1]+12, self.color)
        framebuf.rect(axis[0]+2, axis[1]+22, 104, 8, self.color)
        framebuf.fill_rect(axis[0]+4,axis[1]+24,int(mem_alloc/mem_total * 100),4, self.color)
        
