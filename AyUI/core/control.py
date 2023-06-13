from AyUI.core.event import Event
from AyUI.core.instance import Instance

class ActivityCtrl:
    """用于控制引擎相关"""

    def __init__(self, engine):
        self._engine = engine

    def change(self, activity_name: str):
        """更改当前Activity，这会导致前一个Activity被摧毁"""
        assert type(activity_name) is str, Exception(
            "The 'activity_name' must be string")
        self._engine.commit(Event(Event.CHANGE_ACTIVITY, activity_name))

    def push(self, activity_name: str):
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

    def on(self, event_name: str, callback):
        """注册一个事件监听函数"""
        assert callable(callback), Exception("'callback' should be callable")
        self._instance.event_reg(event_name, callback)