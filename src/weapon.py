from object import *


class Weapon(Object):
    def __init__(self, name: str, dmg: int, crit: int) -> None:
        super().__init__(name)
        self.dmg = dmg
        self.crit = crit

    def __str__(self) -> str:
        return self.name

