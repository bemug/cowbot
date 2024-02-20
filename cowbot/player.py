from cowbot.character import *


class Player(Character):
    scale_factor = 1

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.level = 1
        self.exp = 0
        self.foe_exp = self.exp
        self.base_hp = 16
        self.hp = self.get_max_hp()
        self.base_damage = 6
        self.inventory = []
