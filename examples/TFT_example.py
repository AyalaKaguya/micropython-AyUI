from driver.ST7735 import TFT
from machine import Pin,SPI

def TFTColor(r,g,b) :
  return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)

spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(2), mosi=Pin(3), miso=Pin(10))

tft=TFT(spi,6,10,7) #DC, Reset, CS
tft.initr()
tft.rgb(True)
tft.rotation(1) #方向调整

while True:
    for i in range(255):
        tft.fill(TFTColor(i,255-i,0))
    for i in range(255):
        tft.fill(TFTColor(255-i,0,i))
    for i in range(255):
        tft.fill(TFTColor(0,i,255-i))
        
