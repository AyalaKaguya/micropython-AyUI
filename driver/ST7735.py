# This is a stripped-down ST7735 driver that implements FrameBuffer, 
# and the complete code is https://github.com/boochow/MicroPython-ST7735
#driver for Sainsmart 1.8" TFT display ST7735
#Translated by Guy Carver from the ST7735 sample code.
#Modirfied for micropython-esp32 by boochow 

import machine
import time
from math import sqrt

TFTRotations = [0x00, 0x60, 0xC0, 0xA0]
TFTBGR = 0x08
TFTRGB = 0x00

def clamp( aValue, aMin, aMax ) :
  return max(aMin, min(aMax, aValue))

def TFTColor( aR, aG, aB ) :
  return ((aR & 0xF8) << 8) | ((aG & 0xFC) << 3) | (aB >> 3)

ScreenSize = (128, 160)

class TFT(object) :

  NOP = 0x0
  SWRESET = 0x01
  RDDID = 0x04
  RDDST = 0x09

  SLPIN  = 0x10
  SLPOUT  = 0x11
  PTLON  = 0x12
  NORON  = 0x13

  INVOFF = 0x20
  INVON = 0x21
  DISPOFF = 0x28
  DISPON = 0x29
  CASET = 0x2A
  RASET = 0x2B
  RAMWR = 0x2C
  RAMRD = 0x2E

  VSCRDEF = 0x33
  VSCSAD = 0x37

  COLMOD = 0x3A
  MADCTL = 0x36

  FRMCTR1 = 0xB1
  FRMCTR2 = 0xB2
  FRMCTR3 = 0xB3
  INVCTR = 0xB4
  DISSET5 = 0xB6

  PWCTR1 = 0xC0
  PWCTR2 = 0xC1
  PWCTR3 = 0xC2
  PWCTR4 = 0xC3
  PWCTR5 = 0xC4
  VMCTR1 = 0xC5

  RDID1 = 0xDA
  RDID2 = 0xDB
  RDID3 = 0xDC
  RDID4 = 0xDD

  PWCTR6 = 0xFC

  GMCTRP1 = 0xE0
  GMCTRN1 = 0xE1

  BLACK = 0
  RED = TFTColor(0xFF, 0x00, 0x00)
  MAROON = TFTColor(0x80, 0x00, 0x00)
  GREEN = TFTColor(0x00, 0xFF, 0x00)
  FOREST = TFTColor(0x00, 0x80, 0x80)
  BLUE = TFTColor(0x00, 0x00, 0xFF)
  NAVY = TFTColor(0x00, 0x00, 0x80)
  CYAN = TFTColor(0x00, 0xFF, 0xFF)
  YELLOW = TFTColor(0xFF, 0xFF, 0x00)
  PURPLE = TFTColor(0xFF, 0x00, 0xFF)
  WHITE = TFTColor(0xFF, 0xFF, 0xFF)
  GRAY = TFTColor(0x80, 0x80, 0x80)

  @staticmethod
  def color( aR, aG, aB ) :
    return TFTColor(aR, aG, aB)

  def __init__( self, spi, aDC, aReset, aCS) :
    self._size = ScreenSize
    self._offset = bytearray([0,0])
    self.rotate = 0
    self._rgb = True
    self.tfa = 0
    self.bfa = 0 
    self.dc  = machine.Pin(aDC, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    self.reset = machine.Pin(aReset, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    self.cs = machine.Pin(aCS, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    self.cs(1)
    self.spi = spi
    self.colorData = bytearray(2)
    self.windowLocData = bytearray(4)

  def size( self ) :
    return self._size

  def on( self, aTF = True ) :
    self._writecommand(TFT.DISPON if aTF else TFT.DISPOFF)

  def invertcolor( self, aBool ) :
    self._writecommand(TFT.INVON if aBool else TFT.INVOFF)

  def rgb( self, aTF = True ) :
    self._rgb = aTF
    self._setMADCTL()

  def rotation( self, aRot ) :
    if (0 <= aRot < 4):
      rotchange = self.rotate ^ aRot
      self.rotate = aRot
      if (rotchange & 1):
        self._size =(self._size[1], self._size[0])
      self._setMADCTL()

  def pixel( self, x, y, aColor ) :
    if 0 <= x < self._size[0] and 0 <= y < self._size[1]:
      self._setwindowpoint(x, y)
      self._pushcolor(aColor)

  def text( self, aString, x, y, aColor, aFont, w, h = 1, nowrap = False ) :

    if aFont == None:
      return

    if (type(w, h) == int) or (type(w, h) == float):
      wh = (w, h, w, h)
    else:
      wh = w, h

    px, py = x, y
    width = wh[0] * aFont["Width"] + 1
    for c in aString:
      self.char((px, py), c, aColor, aFont, wh)
      px += width
      if px + width > self._size[0]:
        if nowrap:
          break
        else:
          py += aFont["Height"] * wh[1] + 1
          px = x

  def char( self, x, y, aChar, aColor, aFont, w, hs ) :

    if aFont == None:
      return

    startchar = aFont['Start']
    endchar = aFont['End']

    ci = ord(aChar)
    if (startchar <= ci <= endchar):
      fontw = aFont['Width']
      fonth = aFont['Height']
      ci = (ci - startchar) * fontw

      charA = aFont["Data"][ci:ci + fontw]
      px = x
      if w <= 1 and w <= 1 :
        buf = bytearray(2 * fonth * fontw)
        for q in range(fontw) :
          c = charA[q]
          for r in range(fonth) :
            if c & 0x01 :
              pos = 2 * (r * fontw + q)
              buf[pos] = aColor >> 8
              buf[pos + 1] = aColor & 0xff
            c >>= 1
        self.image(x, y, x + fontw - 1, y + fonth - 1, buf)
      else:
        for c in charA :
          py = y
          for r in range(fonth) :
            if c & 0x01 :
              self.fillrect((px, py), w, hs, aColor)
            py += w, hs[1]
            c >>= 1
          px += w, hs[0]

  def line( self, x, y, x1, y1, aColor ) :
    if x == x1:
      pnt = x1, y1 if (y1 < y) else x, y
      self.vline(pnt, abs(y1 - y) + 1, aColor)
    elif y == y1:
      pnt = x1, y1 if x1 < x else x, y
      self.hline(pnt, abs(x1 - x) + 1, aColor)
    else:
      px, py = x, y
      ex, ey = x1, y1
      dx = ex - px
      dy = ey - py
      inx = 1 if dx > 0 else -1
      iny = 1 if dy > 0 else -1

      dx = abs(dx)
      dy = abs(dy)
      if (dx >= dy):
        dy <<= 1
        e = dy - dx
        dx <<= 1
        while (px != ex):
          self.pixel((px, py), aColor)
          if (e >= 0):
            py += iny
            e -= dx
          e += dy
          px += inx
      else:
        dx <<= 1
        e = dx - dy
        dy <<= 1
        while (py != ey):
          self.pixel((px, py), aColor)
          if (e >= 0):
            px += inx
            e -= dy
          e += dx
          py += iny

  def vline( self, x, y, aLen, aColor ) :
    start = (clamp(x, 0, self._size[0]), clamp(y, 0, self._size[1]))
    stop = (start[0], clamp(start[1] + aLen, 0, self._size[1]))
    if (stop[1] < start[1]):
      start, stop = stop, start
    self._setwindowloc(start, stop)
    self._setColor(aColor)
    self._draw(aLen)

  def hline( self, x, y, aLen, aColor ) :
    start = (clamp(x, 0, self._size[0]), clamp(y, 0, self._size[1]))
    stop = (clamp(start[0] + aLen, 0, self._size[0]), start[1])
    if (stop[0] < start[0]):
      start, stop = stop, start
    self._setwindowloc(start, stop)
    self._setColor(aColor)
    self._draw(aLen)

  def rect( self, x, y, w, h, aColor ) :
    self.hline(x, y, w, aColor)
    self.hline((x, y + h - 1), w, aColor)
    self.vline(x, y, h, aColor)
    self.vline((x + w - 1, y), h, aColor)

  def fillrect( self, x, y, w, h, aColor ) :
    start = (clamp(x, 0, self._size[0]), clamp(y, 0, self._size[1]))
    end = (clamp(start[0] + w - 1, 0, self._size[0]), clamp(start[1] + h - 1, 0, self._size[1]))

    if (end[0] < start[0]):
      tmp = end[0]
      end = (start[0], end[1])
      start = (tmp, start[1])
    if (end[1] < start[1]):
      tmp = end[1]
      end = (end[0], start[1])
      start = (start[0], tmp)

    self._setwindowloc(start, end)
    numPixels = (end[0] - start[0] + 1) * (end[1] - start[1] + 1)
    self._setColor(aColor)
    self._draw(numPixels)

  def circle( self, x, y, aRadius, aColor ) :
    self.colorData[0] = aColor >> 8
    self.colorData[1] = aColor
    xend = int(0.7071 * aRadius) + 1
    rsq = aRadius * aRadius
    for x in range(xend) :
      y = int(sqrt(rsq - x * x))
      xp = x + x
      yp = y + y
      xn = x - x
      yn = y - y
      xyp = x + y
      yxp = y + x
      xyn = x - y
      yxn = y - x

      self._setwindowpoint((xp, yp))
      self._writedata(self.colorData)
      self._setwindowpoint((xp, yn))
      self._writedata(self.colorData)
      self._setwindowpoint((xn, yp))
      self._writedata(self.colorData)
      self._setwindowpoint((xn, yn))
      self._writedata(self.colorData)
      self._setwindowpoint((xyp, yxp))
      self._writedata(self.colorData)
      self._setwindowpoint((xyp, yxn))
      self._writedata(self.colorData)
      self._setwindowpoint((xyn, yxp))
      self._writedata(self.colorData)
      self._setwindowpoint((xyn, yxn))
      self._writedata(self.colorData)

  def fillcircle( self, x, y, aRadius, aColor ) :
    rsq = aRadius * aRadius
    for x in range(aRadius) :
      y = int(sqrt(rsq - x * x))
      y0 = y - y
      ey = y0 + y * 2
      y0 = clamp(y0, 0, self._size[1])
      ln = abs(ey - y0) + 1;

      self.vline((x + x, y0), ln, aColor)
      self.vline((x - x, y0), ln, aColor)

  def fill( self, aColor = BLACK ) :
    self.fillrect((0, 0), self._size, aColor)

  def image( self, x0, y0, x1, y1, data ) :
    self._setwindowloc((x0, y0), (x1, y1))
    self._writedata(data)

  def setvscroll(self, tfa, bfa) :
    self._writecommand(TFT.VSCRDEF)
    data2 = bytearray([0, tfa])
    self._writedata(data2)
    data2[1] = 162 - tfa - bfa
    self._writedata(data2)
    data2[1] = bfa
    self._writedata(data2)
    self.tfa = tfa
    self.bfa = bfa

  def vscroll(self, value) :
    a = value + self.tfa
    if (a + self.bfa > 162) :
      a = 162 - self.bfa
    self._vscrolladdr(a)

  def _vscrolladdr(self, addr) :
    self._writecommand(TFT.VSCSAD)
    data2 = bytearray([addr >> 8, addr & 0xff])
    self._writedata(data2)
    
  def _setColor( self, aColor ) :
    self.colorData[0] = aColor >> 8
    self.colorData[1] = aColor
    self.buf = bytes(self.colorData) * 32

  def _draw( self, aPixels ) :

    self.dc(1)
    self.cs(0)
    for i in range(aPixels//32):
      self.spi.write(self.buf)
    rest = (int(aPixels) % 32)
    if rest > 0:
        buf2 = bytes(self.colorData) * rest
        self.spi.write(buf2)
    self.cs(1)

  def _setwindowpoint( self, x, y ) :
    x = self._offset[0] + int(x)
    y = self._offset[1] + int(y)
    self._writecommand(TFT.CASET)
    self.windowLocData[0] = self._offset[0]
    self.windowLocData[1] = x
    self.windowLocData[2] = self._offset[0]
    self.windowLocData[3] = x
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)
    self.windowLocData[0] = self._offset[1]
    self.windowLocData[1] = y
    self.windowLocData[2] = self._offset[1]
    self.windowLocData[3] = y
    self._writedata(self.windowLocData)
    self._writecommand(TFT.RAMWR)

  def _setwindowloc( self, aPos0, aPos1 ) :
    self._writecommand(TFT.CASET)
    self.windowLocData[0] = self._offset[0]
    self.windowLocData[1] = self._offset[0] + int(aPos0[0])
    self.windowLocData[2] = self._offset[0]
    self.windowLocData[3] = self._offset[0] + int(aPos1[0])
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)
    self.windowLocData[0] = self._offset[1]
    self.windowLocData[1] = self._offset[1] + int(aPos0[1])
    self.windowLocData[2] = self._offset[1]
    self.windowLocData[3] = self._offset[1] + int(aPos1[1])
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RAMWR)  

  def _writecommand( self, aCommand ) :
    self.dc(0)
    self.cs(0)
    self.spi.write(bytearray([aCommand]))
    self.cs(1)

  def _writedata( self, aData ) :
    self.dc(1)
    self.cs(0)
    self.spi.write(aData)
    self.cs(1)

  def _pushcolor( self, aColor ) :
    self.colorData[0] = aColor >> 8
    self.colorData[1] = aColor
    self._writedata(self.colorData)

  def _setMADCTL( self ) :
    self._writecommand(TFT.MADCTL)
    rgb = TFTRGB if self._rgb else TFTBGR
    self._writedata(bytearray([TFTRotations[self.rotate] | rgb]))

  def _reset( self ) :
    self.dc(0)
    self.reset(1)
    time.sleep_us(500)
    self.reset(0)
    time.sleep_us(500)
    self.reset(1)
    time.sleep_us(500)

  def initr( self ) :
    self._reset()

    self._writecommand(TFT.SWRESET)
    time.sleep_us(150)
    self._writecommand(TFT.SLPOUT)
    time.sleep_us(500)

    data3 = bytearray([0x01, 0x2C, 0x2D])
    self._writecommand(TFT.FRMCTR1)
    self._writedata(data3)

    self._writecommand(TFT.FRMCTR2)
    self._writedata(data3)

    data6 = bytearray([0x01, 0x2c, 0x2d, 0x01, 0x2c, 0x2d])
    self._writecommand(TFT.FRMCTR3)
    self._writedata(data6)
    time.sleep_us(10)

    data1 = bytearray(1)
    self._writecommand(TFT.INVCTR)
    data1[0] = 0x07
    self._writedata(data1)

    self._writecommand(TFT.PWCTR1)
    data3[0] = 0xA2
    data3[1] = 0x02
    data3[2] = 0x84
    self._writedata(data3)

    self._writecommand(TFT.PWCTR2)
    data1[0] = 0xC5
    self._writedata(data1)

    data2 = bytearray(2)
    self._writecommand(TFT.PWCTR3)
    data2[0] = 0x0A
    data2[1] = 0x00
    self._writedata(data2)

    self._writecommand(TFT.PWCTR4)
    data2[0] = 0x8A
    data2[1] = 0x2A
    self._writedata(data2)

    self._writecommand(TFT.PWCTR5)
    data2[0] = 0x8A
    data2[1] = 0xEE
    self._writedata(data2)

    self._writecommand(TFT.VMCTR1)
    data1[0] = 0x0E
    self._writedata(data1)

    self._writecommand(TFT.INVOFF)

    self._writecommand(TFT.MADCTL)
    data1[0] = 0xC8
    self._writedata(data1)

    self._writecommand(TFT.COLMOD)
    data1[0] = 0x05
    self._writedata(data1)

    self._writecommand(TFT.CASET)
    self.windowLocData[0] = 0x00
    self.windowLocData[1] = 0x00
    self.windowLocData[2] = 0x00
    self.windowLocData[3] = self._size[0] - 1
    self._writedata(self.windowLocData)

    self._writecommand(TFT.RASET)
    self.windowLocData[3] = self._size[1] - 1
    self._writedata(self.windowLocData)

    dataGMCTRP = bytearray([0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f,
                            0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10])
    self._writecommand(TFT.GMCTRP1)
    self._writedata(dataGMCTRP)

    dataGMCTRN = bytearray([0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30,
                            0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10])
    self._writecommand(TFT.GMCTRN1)
    self._writedata(dataGMCTRN)
    time.sleep_us(10)

    self._writecommand(TFT.DISPON)
    time.sleep_us(100)

    self._writecommand(TFT.NORON)
    time.sleep_us(10)

    self.cs(1)
