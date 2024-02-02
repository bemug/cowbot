from item import *


class Armor(Item):
    def __init__(self, name: str, arm: int, miss: int) -> None:
        super().__init__(name)
        self.arm = arm
        self.miss = miss

    def __str__(self) -> str:
        return self.name

