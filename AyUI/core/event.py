from micropython import const

class Event:
    """事件类"""
    PUSH_ACTIVITY = const(0x00)
    POP_ACTIVITY = const(0x01)
    CHANGE_ACTIVITY = const(0x02)

    BUTTON_CLICK = const("click")

    def __init__(self, event: str, payload: object = None):
        self.event = event
        self.payload = payload