import uasyncio
import time
from micropython import const
import gc


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


class View:
    """基本视图"""
    def draw(self, framebuf, axis=(0, 0)):
        """绘图函数，用于绘制视图和所有子元素"""
        pass

    def calc(self, f_space=(0, 0)):
        """计算函数，计算绘制空间，传入可用空间，传出占用空间"""
        return (0, 0)


class Event:
    """事件类"""
    PUSH_ACTIVITY = const(0x00)
    POP_ACTIVITY = const(0x01)
    CHANGE_ACTIVITY = const(0x02)

    BUTTON_CLICK = const("click")

    def __init__(self, event, payload=None):
        self.event = event
        self.payload = payload


class Instance:
    """用于保存当前Activity的状态，以及Event的路由，不应该直接操作Instance类而是通过EventCtrl类间接操作"""

    def __init__(self, activity_name):
        self.activity = None
        self.view = None
        self.event_calls = dict()
        self.name = activity_name

    def event_reg(self, event, callback):
        """注册一个事件"""
        if not event in self.event_calls:
            self.event_calls[event] = list()

        self.event_calls[event].append(callback)

    def event_exec(self, event, payload=None):
        """调用当前Activity注册过的事件"""
        if not event in self.event_calls:
            return
        for i in self.event_calls[event]:
            try:
                i(payload)
            except TypeError:
                print("[WARN] Event callback requires a parameter to be specified")
            except Exception as ex:
                print("[WARN] Event callback has create en exception")
                print(ex)


class ActivityCtrl:
    """用于控制引擎相关"""

    def __init__(self, engine):
        self._engine = engine

    def change(self, activity_name):
        """更改当前Activity，这会导致前一个Activity被摧毁"""
        assert type(activity_name) is str, Exception(
            "The 'activity_name' must be string")
        self._engine.commit(Event(Event.CHANGE_ACTIVITY, activity_name))

    def push(self, activity_name):
        """创建并进入一个Activity"""
        assert type(activity_name) is str, Exception(
            "The 'activity_name' must be string")
        self._engine.commit(Event(Event.PUSH_ACTIVITY, activity_name))

    def pop(self):
        """返回上一个Activity"""
        self._engine.commit(Event(Event.POP_ACTIVITY))

    def create_event(self, event: Event):
        """创建一个事件"""
        self._engine.commit(event)


class EventCtrl:
    """用于控制事件接收相关"""

    def __init__(self, instance: Instance):
        self._instance = instance

    def on(self, event_name, callback):
        """注册一个事件监听函数"""
        assert callable(callback), Exception("'callback' should be callable")
        self._instance.event_reg(event_name, callback)


class Activity:
    """Activity 类，实现页面办法的基类"""

    def __init__(self, activity_ctrl: ActivityCtrl, event_ctrl: EventCtrl):
        self.activity = activity_ctrl
        self.event = event_ctrl

    def onCreate(self):
        """当Activity被创建并实例化后执行"""
        pass

    def onDestroy(self):
        """当Activity被删除前执行"""
        pass

    def onStart(self):
        """当Activity进入前台前执行"""
        pass

    def view(self, space):
        return View()


class Engine:
    """AyUI渲染引擎"""
    enable = True

    def __init__(self, width: int, height: int, root_framebuf, draw_exec, gc_flag=False):
        self.width = width
        self.height = height
        self.framebuf = root_framebuf
        self.draw_exec = draw_exec
        self.gc = gc_flag
        self.instances = []  # 页面数据
        self.registry = dict()  # Activity 注册
        self.events = []  # 全局事件列表
        gc.enable()

    def register(self, name, activity):
        """注册一个activity"""
        assert type(name) is str, Exception("The 'name' must be string")
        assert issubclass(activity, Activity), TypeError(
            "'activity' is not a vaild Activity class")
        self.registry[name] = activity

    def register_activity(self, name):
        """注册一个activity"""
        assert type(name) is str, Exception("The 'name' must be string")

        def reg(activity):
            assert issubclass(activity, Activity), TypeError(
                "'activity' is not a vaild Activity class")
            self.register(name, activity)
            return activity
        return reg

    def create_activity(self, activity_name):
        """创建一个activity"""
        assert type(activity_name) is str, Exception(
            "The 'activity_name' must be string")
        activity = self.registry[activity_name]  # 从注册列表获取Activity类
        instance = Instance(activity_name)      # 创建一个Instance用于保存信息
        actctrl = ActivityCtrl(self)            # 创建一个Activity控制器
        evtctrl = EventCtrl(instance)           # 创建一个Event控制器
        # 实例化获取的Activity类并链接到Instance
        instance.activity = activity(actctrl, evtctrl)
        instance.view = instance.activity.view(
            space=(self.width, self.height)
        )
        self.instances.append(instance)         # 添加Instance到列表
        instance.activity.onCreate()

    def destroy_activity(self, index=None):
        """删除一个activity"""
        if index is None:
            index = -1
        self.instances[index].activity.onDestroy()
        del self.instances[index].activity.activity
        del self.instances[index].activity.event
        del self.instances[index].activity
        del self.instances[index]

    def start_activity_from(self, activity_name):
        """启动一个activity，一般用于定义最开始的activity"""
        assert type(activity_name) is str, Exception(
            "The 'activity_name' must be string")
        self.events.append(Event(Event.PUSH_ACTIVITY, activity_name))

    def commit(self, event):
        """创建一个事件，事件来自类Event"""
        assert isinstance(event, Event), TypeError(
            "'event' is not a vaild Event class")
        self.events.append(event)

    def handle_events(self):
        """处理上一帧发生的事件"""
        if len(self.events) == 0:
            return
        events = self.events.copy()
        self.events = []
        for i in events:
            # 处理ActivityCtrl
            if i.event == Event.CHANGE_ACTIVITY:
                # 更改Activity(onDestroy,onCreate)
                self.destroy_activity(-1)
                self.create_activity(i.payload)
                self.instances[-1].activity.onStart()
                break
            elif i.event == Event.POP_ACTIVITY:
                # 退出Activity(onDestroy)
                assert len(self.instances) > 0, Exception(
                    "No Activity can exit")
                self.destroy_activity(-1)
                if len(self.instances) == 0:
                    print("[WARN] The last activity exited!")
                else:
                    self.instances[-1].activity.onStart()
                break
            elif i.event == Event.PUSH_ACTIVITY:
                # 新建Activity(onCreate)
                self.create_activity(i.payload)
                self.instances[-1].activity.onStart()
                break
            else:
                # 处理EventCtrl 调用Activity注册的回调函数
                self.instances[-1].event_exec(i.event, i.payload)
        del events

    def draw(self):
        """将当前帧渲染至framebuf"""
        self.framebuf.fill(0)
        if len(self.instances) == 0:
            return
        # TODO Activity 渲染阶段
        self.instances[-1].view.calc(f_space=(self.width, self.height))
        self.instances[-1].view.draw(self.framebuf)

        mem_free = gc.mem_alloc()
        mem_total = 111168
        self.framebuf.text("mem: %d %%" %
                           (int(mem_free*100/mem_total)), 2, 2, 1)
        self.framebuf.rect(0, 0, int(mem_free/mem_total * 128), 64, 1)

    async def start(self, target_fps):
        """启动UI线程和帧循环"""
        print("[INFO] AyUI: The UI thread starts")
        frame_target = int(1000/target_fps)
        while self.enable:
            for i in range(target_fps):
                frame_start = time.ticks_ms()
                self.handle_events()
                self.draw()
                self.draw_exec()
                frame_total = time.ticks_diff(time.ticks_ms(), frame_start)
                if frame_total > frame_target:
                    print("[WARN] Can`t keep up, is it overloaded?")
                else:
                    await uasyncio.sleep_ms(frame_target-frame_total)
            # 大概是每秒钟这里会被执行一次
            if self.gc:
                gc.collect()
        print("[WARN] ui.engine has been closed!")
