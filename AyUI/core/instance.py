

class Instance:
    """用于保存当前Activity的状态，以及Event的路由，不应该直接操作Instance类而是通过EventCtrl类间接操作"""

    def __init__(self, activity_name:str):
        self.activity = None
        self.view = None
        self.event_calls = dict()
        self.name = activity_name

    def event_reg(self, event: str, callback):
        """注册一个事件"""
        if not event in self.event_calls:
            self.event_calls[event] = list()

        self.event_calls[event].append(callback)

    def event_exec(self, event: str, payload=None):
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