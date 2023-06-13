import uasyncio
import time
import gc

from AyUI.core.event import Event
from AyUI.core.activity import Activity
from AyUI.core.view import View
from AyUI.core.instance import Instance
from AyUI.core.control import ActivityCtrl, EventCtrl

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
        if gc_flag:
            gc.enable()

    def register(self, name: str, activity):
        """注册一个activity"""
        assert type(name) is str, Exception("The 'name' must be string")
        assert issubclass(activity, Activity), TypeError(
            "'activity' is not a vaild Activity class")
        self.registry[name] = activity

    def register_activity(self, name: str):
        """注册一个activity"""
        assert type(name) is str, Exception("The 'name' must be string")

        def reg(activity):
            assert issubclass(activity, Activity), TypeError(
                "'activity' is not a vaild Activity class")
            self.register(name, activity)
            return activity
        return reg

    def create_activity(self, activity_name: str):
        """创建一个activity"""
        assert type(activity_name) is str, Exception(
            "The 'activity_name' must be string")
        activity = self.registry[activity_name]  # 从注册列表获取Activity类
        instance = Instance(activity_name)      # 创建一个Instance用于保存信息
        actctrl = ActivityCtrl(self)            # 创建一个Activity控制器
        evtctrl = EventCtrl(instance)           # 创建一个Event控制器
        instance.activity = activity(actctrl, evtctrl)
        self.instances.append(instance)
        instance.activity.onCreate()
        view = instance.activity.view(
            space=(self.width, self.height)
        )
        assert isinstance(view, View), TypeError(
            "[ERR] in activity {}, view() returned an incorrect type".format(activity_name))
        instance.view = view

    def destroy_activity(self, index: int = None):
        """删除一个activity"""
        if index is None:
            index = -1
        self.instances[index].activity.onDestroy()
        del self.instances[index].activity.activity
        del self.instances[index].activity.event
        del self.instances[index].activity
        del self.instances[index]

    def start_activity_from(self, activity_name: str):
        """启动一个activity，一般用于定义最开始的activity"""
        assert type(activity_name) is str, TypeError(
            "The 'activity_name' must be string")
        self.events.append(Event(Event.PUSH_ACTIVITY, activity_name))

    def commit(self, event: Event):
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
        # Activity 渲染阶段
        self.instances[-1].activity.beforeFrame()
        self.instances[-1].view.calc(f_space=(self.width, self.height))
        self.instances[-1].view.draw(self.framebuf)
        self.instances[-1].activity.afterFrame()

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
