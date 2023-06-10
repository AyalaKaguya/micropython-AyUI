# 这是适用于合宙air103小显示屏的示例代码
from machine import Pin,SPI
import driver.AIR103TFT as TFT

spi = SPI(1, baudrate=20000000, polarity=0, phase=0, sck=Pin(2), mosi=Pin(3), miso=Pin(10))

tft = TFT.Builder(rgb=True)\
               .set_spi(spi)\
               .set_size(160, 80)\
               .set_size_offset(0,24)\
               .set_cs_pin(7)\
               .set_dc_pin(6)\
               .set_reset_pin(10)\
               .build()
               
tft.fill(0)
tft.show()


# 绘制背景色
tft.fill(TFT.RGB(255,0,0))

# 绘制方块
tft.fill_rect(140,60,20,20,TFT.RGB(0,0,255))
tft.fill_rect(0,0,20,20,TFT.RGB(0,255,0))
tft.fill_rect(140,0,20,20,TFT.RGB(0,255,255))
tft.fill_rect(0,60,20,20,TFT.RGB(255,255,0))

tft.show()