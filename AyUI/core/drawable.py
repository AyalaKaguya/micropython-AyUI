

class Drawable:
    """基本绘画元素"""

    @property
    def width(self):
        return 0

    @property
    def height(self):
        return 0

    def draw(self, framebuf, axis):
        pass