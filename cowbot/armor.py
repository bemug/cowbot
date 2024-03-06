from cowbot.wearable import *


class Armor(Wearable):
    def __init__(self, name: str, armor: int, miss: int) -> None:
        super().__init__(name)
        self.armor = armor
        self.miss = miss
