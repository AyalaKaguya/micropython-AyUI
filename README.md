# AyUI

一个现代的，极简的，易于扩展的UI框架，基于MicroPython和FrameBuffer，支持事件驱动。

完成度 60%

架构图： Engine -> Activity -> View -> DrawAble

目前的架构下存在未知的内存泄漏，初步怀疑内存泄漏来自于uasyncio，如果担心内存泄漏问题的可以选择直接调用Engine.start方法或者在多核心上使用_thread库

## Activity 活动

Activity将会收到以下方法：

- self.activity.change()    切换当前的Activity
- self.activity.push()      新增一个Activity，挂起上一个Activity
- self.activity.pop()       退出当前Activity并删除实例，返回上一个Activity
- self.activity.create_event()    创建一个事件，由Engine接收
- self.event.on()           注册事件监听器并绑定当前Activity

以上操作都基于帧，**当前帧产生的各种事件都会在下一帧开始前运行**，并且Activity重写优先于Event监听，该特性要求后端服务程序尽量不要占用过长时间，当触发Activity变化时，余下的Event将不会再触发。

Activity事件重写一共有三种：`onCreate`、`onDestroy`和`onStart`，分别对应Activity创建、Activity销毁和Activity启动，其中`onCreate`事件和`onDestroy`事件在整个Activity生命周期内只会被调用一次，而`onStart`事件只要切换到当前Activity就会触发一次。

**TODO**: 绘图部分尚未完成

Activity上面将绑定一个View，采用渲染序列的方式渲染，View可以操纵该渲染序列。
这个View将通过函数式（声明式）的方式完成定义，以此达成数据绑定。

## Engine 引擎

Engine 负责Activity的注册和切换，以及Event的监听和路由。
AyUI的所有事情将起源于此，当我们初始化时提供以下参数：

```python
from ayui import Engine

engine = Engine(width,height,framebuf,draw_exec)
```

- width: 目标FrameBuffer的宽
- height: 目标FrameBuffer的高
- framebuf: FrameBuffer对象
- draw_exec: 绘图回调，每一帧绘制结束调用

Engine提供一个装饰器供注册Activity使用，而所有的Activity必须先注册才能被使用：

```python
@engine.register_activity("MainActivity")
class MainActivity(Activity):
    def onCreate(self):
        print("MainActivity Create")
        self.activity.push("SecondActivity")
        
    def onStart(self):
        print("MainActivity Start")
```

当然你也可以这样使用：

```python
class MainActivity(Activity):
    def onCreate(self):
        print("MainActivity Create")
        self.activity.push("SecondActivity")
        
    def onStart(self):
        print("MainActivity Start")

engine.register("MainActivity", MainActivity)
```

你需要指定哪个Activity最先启动，使用以下方法：

```python
engine.start_activity_from("MainActivity")
```

启动引擎：

```python
import uasyncio

uasyncio.run(engine.start(target_fps= 20))
```

目前Engine所有的函数都是公开的，但这并不意味着你可以随意的调用它们，至少目前阶段这样的调用是无法被预见的。

## Event 事件

除了Active可以创建事件，在**异步**的`Engine`上可以调用`commit`方法来产生事件，如果你的异步符合规范，那么你的代码将会在每帧渲染的间隙得以执行，这意味这事件的产生是线程安全的。

```python
...
@engine.register_activity("MainActivity")
class MainActivity(Activity):
    def onCreate(self):
        print("MainActivity Create")
        self.event.on("click", self.onClick)
        
    def onStart(self):
        print("MainActivity Start")

    def onClick(self, payload):
        print("clink", payload)
...
async def app_main():
    while True:
        engine.commit('click', 'home')
        await uasyncio.sleep_ms(2000)
...
uasyncio.create_task(engine.start(target_fps= 20))
uasyncio.create_task(app_main())
uasyncio.get_event_loop().run_forever()
```

这应该会每两秒输出 `click home`

## 举个例子

**生命周期**

```python 
from machine import Pin,I2C
from driver.SSD1306 import SSD1306_I2C
from ayui import Engine,Activity
import uasyncio

i2c = I2C(0)
oled = SSD1306_I2C(128, 64, i2c)

engine = Engine(oled.width,oled.height,oled,oled.show)

@engine.register_activity("MainActivity")
class MainActivity(Activity):
    def onCreate(self):
        print("MainActivity Create")
        self.activity.push("SecondActivity")
        
    def onStart(self):
        print("MainActivity Start")
        
@engine.register_activity("SecondActivity")
class SecondActivity(Activity):
    def onCreate(self):
        print("SecondActivity Create")
        
    def onStart(self):
        print("SecondActivity Start")
        self.activity.pop()

engine.start_activity_from("MainActivity")

uasyncio.create_task(engine.start(target_fps= 20))
# 你可以在这里创建其他的异步任务以扩展事件等功能
uasyncio.get_event_loop().run_forever()

""" output
[INFO] AyUI: The UI thread starts
MainActivity Create
MainActivity Start
SecondActivity Create
SecondActivity Start
MainActivity Start
"""
```

**绘图实例**

实时显示内存占用，这应该会有一个白色的大框包裹一段红色的信息：

```python
from AyUI import Activity
from AyUI.views.basic import BasicView
from AyUI.widgets.memtest import Memtest

@engine.register_activity("MainActivity")
class MainActivity(Activity):
    def view(self, space):
        return BasicView(
            Memtest(tft.rgb(255,0,0)),
            
            space = (space[0]-2,space[1]-2),
            margin= (0,0,0,0),
            padding=(2,2,2,2),
            border = 1,
            border_color = tft.rgb(255,255,255)
        )
    
    def onCreate(self):
        print("MainActivity onCreate")

    def onStart(self):
        print("MainActivity onStart")
```
