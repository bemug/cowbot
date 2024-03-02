from cowbot.character import *


class Player(Character):
    scale_factor = 1
    inventory_size = 10

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.level = 1
        self.exp = 0
        self.foe_exp = self.exp
        self.base_hp = 16
        self.hp = self.get_max_hp()
        self.base_damage = 6
        self.inventory = {}

    def next_slot(self):
        i = 0
        while i in self.inventory:
            i += 1
        return i

    def get_slot(self, item):
        for index, value in self.inventory.items():
            if value == item:
                return index
        raise ValueError

    def pack_inventory(self):
        i = 0
        old_inv = self.inventory.copy()
        self.inventory.clear()
        for value in old_inv.values():
            self.inventory[i] = value
            i += 1
        return i
