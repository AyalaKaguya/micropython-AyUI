from AyUI.core.control import ActivityCtrl, EventCtrl
from AyUI import View


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