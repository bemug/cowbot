from peakcurve import *
from weapon import *
from armor import *


class Lootable():
    def __init__(self, name, type, loot_chance, attr_list, attr_chance):
        self.name = name
        self.type = type
        self.loot_chance = loot_chance
        self.attr_list = attr_list
        self.attr_chance = attr_chance

    def generate_item(self, value):
        #Avoid tracing if no chance at all
        if self.loot_chance.get_probability(value) == 0:
            return
        trace(f"Attempt to loot '{self}' (lvl. {value})")
        if self.loot_chance.draw_at(value):
            return self.type(self.name, self.attr_list[0], self.attr_list[1])

    def __str__(self) -> str:
        return self.name


lootables = (
        #Weapons
        Lootable("Gun 1", Weapon, PeakCurve(0,0,5), [2,0], [PeakCurve(0,0,3)]),
        Lootable("Gun 2", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gun 2", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gun 2", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gun 2", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        #Armors
    )
