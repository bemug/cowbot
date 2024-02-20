from cowbot.item import *


class Wearable(Item):
    def __init__(self, name: str, attr1: int, attr2: int) -> None:
        super().__init__(name)
        self.attr1 = attr1
        self.attr2 = attr2
