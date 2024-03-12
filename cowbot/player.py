from cowbot.character import *
from cowbot.utils import trace


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
        return -1

    def pack_inventory(self):
        i = 0
        old_inv = self.inventory.copy()
        self.inventory.clear()
        for value in old_inv.values():
            self.inventory[i] = value
            i += 1
        return i

    def swap_inventory(self, slot1, slot2):
        #There must be a better way somehow
        item_slot1 = self.inventory.get(slot1)
        item_slot2 = self.inventory.get(slot2)
        if item_slot1 == None and item_slot2 == None:
            raise ValueError
        elif item_slot1 == None:
            self.inventory[slot1] = self.inventory[slot2]
            del self.inventory[slot2]
        elif item_slot2 == None:
            self.inventory[slot2] = self.inventory[slot1]
            del self.inventory[slot1]
        else:
            self.inventory[slot1], self.inventory[slot2] = self.inventory[slot2], self.inventory[slot1]
        trace("Inventory : " + str(self.inventory))

    def get_inventory_usage(self):
        return f"{len(self.inventory)}/{Player.inventory_size}"
