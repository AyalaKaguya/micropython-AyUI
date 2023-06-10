import machine
import time
import framebuf
from ST7735 import TFT


def RGB(r, g, b):
    '''Create a 16 bit rgb value from the given R,G,B from 0-255.
       This assumes rgb 565 layout and will be incorrect for bgr.'''
    return ((r & 0xF8) << 8) | ((b & 0xFC) << 3) | (g >> 3)


class Builder():
    def __init__(self, rgb=True):
        self.rgb = rgb
        self.spi = None
        self.size = None
        self.size_offset = (0, 0)
        self.cs = None
        self.dc = None
        self.reset = None

    def set_spi(self, spi):
        self.spi = spi
        return self

    def set_size(self, size_w, size_h):
        self.size = (size_w, size_h)
        return self

    def set_size_offset(self, size_offset_w, size_offset_h):
        self.size_offset = (size_offset_w, size_offset_h)
        return self

    def set_cs_pin(self, cs_pin):
        self.cs = cs_pin
        return self

    def set_dc_pin(self, dc_pin):
        self.dc = dc_pin
        return self

    def set_reset_pin(self, reset_pin):
        self.reset = reset_pin
        return self

    def build(self):
        if (self.spi and self.size and self.cs and self.dc and self.reset):
            return TFT_SPI(
                self.size,
                self.size_offset,
                self.rgb,
                self.spi,
                self.cs,
                self.dc,
                self.reset)
        else:
            raise TypeError("Insufficient parameters.")


class TFT_SPI(framebuf.FrameBuffer):
    def __init__(self, size, size_offset, color_mode, spi, cs, dc, reset):
        self.rotate = 1
        self.buffer = bytearray(size[0] * size[1] * 2)
        super().__init__(self.buffer, size[0], size[1], framebuf.RGB565)
        print("[WARN]RGB565: There may be display issues with this color format")
        
        tft = TFT(spi, dc, reset, cs)
        tft.initr()
        tft.rgb(color_mode)
        tft.rotation(1)
        tft._setwindowloc((size_offset[0],size_offset[1]),
                          (size_offset[0]+size[0]-1,size_offset[1]+size[1]-1))
        self.tft = tft
        
    def show(self):
        self.tft._writedata(self.buffer)

