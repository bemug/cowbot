from cowbot.wearable import *


class Weapon(Wearable):
    def __init__(self, name: str, damage: int, critical: int) -> None:
        super().__init__(name)
        self.damage = damage
        self.critical = critical
