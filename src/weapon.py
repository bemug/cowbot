from object import *


class Weapon(Object):
    def __init__(self, name: str, damage: int, critical: int) -> None:
        super().__init__(name)
        self.damge = damage
        self.critical = critical

    def __str__(self) -> str:
        return self.name
        
