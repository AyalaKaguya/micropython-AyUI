

class View:
    """基本视图"""
    def draw(self, framebuf, axis=(0, 0)):
        """绘图函数，用于绘制视图和所有子元素"""
        pass

    def calc(self, f_space=(0, 0)):
        """计算函数，计算绘制空间，传入可用空间，传出占用空间"""
        return (0, 0)