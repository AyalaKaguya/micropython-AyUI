import machine
import time
import framebuf
from micropython import const

# TFT控制位
NOP = const(0x0)
SWRESET = const(0x01)
RDDID = const(0x04)
RDDST = const(0x09)
SLPIN = const(0x10)
SLPOUT = const(0x11)
PTLON = const(0x12)
NORON = const(0x13)
INVOFF = const(0x20)
INVON = const(0x21)
DISPOFF = const(0x28)
DISPON = const(0x29)
CASET = const(0x2A)
RASET = const(0x2B)
RAMWR = const(0x2C)
RAMRD = const(0x2E)
VSCRDEF = const(0x33)
VSCSAD = const(0x37)
COLMOD = const(0x3A)
MADCTL = const(0x36)
FRMCTR1 = const(0xB1)
FRMCTR2 = const(0xB2)
FRMCTR3 = const(0xB3)
INVCTR = const(0xB4)
DISSET5 = const(0xB6)
PWCTR1 = const(0xC0)
PWCTR2 = const(0xC1)
PWCTR3 = const(0xC2)
PWCTR4 = const(0xC3)
PWCTR5 = const(0xC4)
VMCTR1 = const(0xC5)
RDID1 = const(0xDA)
RDID2 = const(0xDB)
RDID3 = const(0xDC)
RDID4 = const(0xDD)
PWCTR6 = const(0xFC)
GMCTRP1 = const(0xE0)
GMCTRN1 = const(0xE1)


# TFTRotations and TFTRGB are bits to set
# on MADCTL to control display rotation/color layout
# Looking at display with pins on top.
# 00 = upper left printing right
# 10 = does nothing (MADCTL_ML)
# 20 = upper left printing down (backwards) (Vertical flip)
# 40 = upper right printing left (backwards) (X Flip)
# 80 = lower left printing right (backwards) (Y Flip)
# 04 = (MADCTL_MH)

# 60 = 90 right rotation
# C0 = 180 right rotation
# A0 = 270 right rotation
TFTRotations = [0x00, 0x60, 0xC0, 0xA0]
TFTBGR = 0x08  # When set color is bgr else rgb.
TFTRGB = 0x00


def RGB(aR, aG, aB):
    '''Create a 16 bit rgb value from the given R,G,B from 0-255.
       This assumes rgb 565 layout and will be incorrect for bgr.'''
    return ((aR & 0xF8) << 8) | ((aG & 0xFC) << 3) | (aB >> 3)


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

    def set_size(self, size_h, size_w):
        self.size = (size_h, size_w)
        return self

    def set_size_offset(self, size_offset_h, size_offset_w):
        self.size_offset = (size_offset_h, size_offset_w)
        return self

    def set_cs_pin(self, cs_pin):
        self.cs = machine.Pin(cs_pin, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        return self

    def set_dc_pin(self, dc_pin):
        self.dc = machine.Pin(dc_pin, machine.Pin.OUT, machine.Pin.PULL_DOWN)
        return self

    def set_reset_pin(self, reset_pin):
        self.reset = machine.Pin(
            reset_pin, machine.Pin.OUT, machine.Pin.PULL_DOWN)
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
        self.rotate = 0
        self.width = size[1]
        self.height = size[0]
        self._size_offset = size_offset
        self._color_mode = color_mode
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.height, self.width, framebuf.RGB565)
        self.dc = dc
        self.cs = cs
        self.cs(1)
        self.reset = reset
        self.spi = spi
        self.windowLocData = bytearray(4)
        self.init_display()

    def poweroff(self):
        self.write_cmd(DISPOFF)
        
    def poweron(self):
        self.write_cmd(DISPON)

    def invert(self, invert):
        self.write_cmd(INVON if invert else INVOFF)

    def show(self):
        self.write_data(self.buffer)

    def write_cmd(self, cmd):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def init_display(self):
        # hard reset
        self.dc(0)
        self.reset(1)
        time.sleep_us(500)
        self.reset(0)
        time.sleep_us(500)
        self.reset(1)
        time.sleep_us(500)

        self.write_cmd(SWRESET)  # Software reset.
        time.sleep_us(150)
        self.write_cmd(SLPOUT)  # out of sleep mode.
        time.sleep_us(500)

        # fastest refresh, 6 lines front, 3 lines back.
        data3 = bytearray([0x00, 0x06, 0x03]) 
        self.write_cmd(FRMCTR1)  # Frame rate control.
        self.write_data(data3)

        self.write_cmd(FRMCTR2)  # Frame rate control.
        self.write_data(data3)

        data6 = bytearray([0x01, 0x2c, 0x2d, 0x01, 0x2c, 0x2d])
        self.write_cmd(FRMCTR3)  # Frame rate control.
        self.write_data(data6)
        time.sleep_us(10)

        data1 = bytearray(1)
        self.write_cmd(INVCTR)  # Display inversion control
        data1[0] = 0x07  # Line inversion.
        self.write_data(data1)

        self.write_cmd(PWCTR1)  # Power control
        data3[0] = 0xA2
        data3[1] = 0x02
        data3[2] = 0x84
        self.write_data(data3)

        self.write_cmd(PWCTR2)  # Power control
        data1[0] = 0xC5  # VGH = 14.7V, VGL = -7.35V
        self.write_data(data1)

        data2 = bytearray(2)
        self.write_cmd(PWCTR3)  # Power control
        data2[0] = 0x0A  # Opamp current small
        data2[1] = 0x00  # Boost frequency
        self.write_data(data2)

        self.write_cmd(PWCTR4)  # Power control
        data2[0] = 0x8A  # Opamp current small
        data2[1] = 0x2A  # Boost frequency
        self.write_data(data2)

        self.write_cmd(PWCTR5)  # Power control
        data2[0] = 0x8A  # Opamp current small
        data2[1] = 0xEE  # Boost frequency
        self.write_data(data2)

        self.write_cmd(VMCTR1)  # Power control
        data1[0] = 0x0E
        self.write_data(data1)

        self.write_cmd(INVOFF)

        self.write_cmd(MADCTL)  # Power control
        data1[0] = 0xC8
        self.write_data(data1)

        self.write_cmd(COLMOD)
        data1[0] = 0x05
        self.write_data(data1)

        self.write_cmd(CASET)  # Column address set.
        self.windowLocData[0] = 0x00
        self.windowLocData[1] = 0x00
        self.windowLocData[2] = 0x00
        self.windowLocData[3] = self.height - 1
        self.write_data(self.windowLocData)

        self.write_cmd(RASET)  # Row address set.
        self.windowLocData[3] = self.width - 1
        self.write_data(self.windowLocData)

        dataGMCTRP = bytearray([0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f,
                                0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])
        self.write_cmd(GMCTRP1)
        self.write_data(dataGMCTRP)

        dataGMCTRN = bytearray([0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30,
                                0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10])
        self.write_cmd(GMCTRN1)
        self.write_data(dataGMCTRN)
        time.sleep_us(10)

        self.write_cmd(DISPON)
        time.sleep_us(100)

        self.write_cmd(NORON)  # Normal display on.
        time.sleep_us(10)

        self.cs(1)

        # set MADCT
        self.write_cmd(MADCTL)
        rgb = TFTRGB if self._color_mode else TFTBGR
        self.write_data(bytearray([TFTRotations[self.rotate] | rgb]))

        # set windowloc
        self.write_cmd(CASET)  # Column address set.
        self.windowLocData[0] = 0x00
        self.windowLocData[1] = int(self._size_offset[0])
        self.windowLocData[2] = 0x00
        self.windowLocData[3] = int(self._size_offset[0] + self.height -1)
        self.write_data(self.windowLocData)

        self.write_cmd(RASET)  # Row address set.
        self.windowLocData[0] = 0x00
        self.windowLocData[1] = int(self._size_offset[1])
        self.windowLocData[2] = 0x00
        self.windowLocData[3] = int(self._size_offset[1] + self.width -1)
        self.write_data(self.windowLocData)

        self.write_cmd(RAMWR)  # Write to RAM.
