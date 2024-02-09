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
        #Require at least level 2 to spawn
        # 8 6 4 2 1
        Lootable("Pistolet de poche Derringer", Weapon, PeakCurve(2,2,5),        [1],     [PeakCurve(0,0,6)]),
        Lootable("Revolver Colt",               Weapon, PeakCurve(2,10,15),      [3],     [PeakCurve(0,0,10)),
        Lootable("Revolver Remington",          Weapon, PeakCurve(2,11,15),      [2,5],   [PeakCurve(0,0,8),  PeakCurve(0,0,10)]),
        Lootable("Revolver S&W",                Weapon, PeakCurve(12,16,20),     [5],     [PeakCurve(0,0,6)),
        Lootable("Pistolet Volcanic",           Weapon, PeakCurve(12,17,20),     [3,10],  [PeakCurve(0,0,10), PeakCurve(0,0,10)]),
        Lootable("Fusil Spencer",               Weapon, PeakCurve(18,20,22),     [6,0],   [PeakCurve(0,0,10), PeakCurve(0,0,6)]),
        Lootable("Fusil Sharps",                Weapon, PeakCurve(18,21,22),     [4,15],  [PeakCurve(0,0,15), PeakCurve(0,0,10)]),
        Lootable("Fusil Springfield",           Weapon, PeakCurve(20,22,24),     [10,5],  [PeakCurve(0,0,15), PeakCurve(0,0,10)]),
        Lootable("Carabine Mauser",             Weapon, PeakCurve(20,23,24),     [5,20],  [PeakCurve(0,0,15), PeakCurve(0,0,15)]),
        Lootable("Carabine Winchester",         Weapon, PeakCurve(23,25,25),     [15,10], [PeakCurve(0,0,20), PeakCurve(0,0,20)]),
        Lootable("Mitrailleuse Gatling",        Weapon, PeakCurve(10,25,25,0.1), [0,40],  [PeakCurve(0,0,1),  PeakCurve(0,0,20)]),
        ### Armors
        #Require at least level 4 to spawn
        # 7 5 4 3 2
        Lootable("Open crease",      Armor, PeakCurve(4,4,7), [1],   [PeakCurve(0,0,5)]),
        Lootable("Cattleman crease", Armor, PeakCurve(4,11,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Cutter crease",    Armor, PeakCurve(3,12,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Ridgetop crease",  Armor, PeakCurve(3,16,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Dakota crease",    Armor, PeakCurve(3,17,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Montana crease",   Armor, PeakCurve(3,20,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gus crease",       Armor, PeakCurve(3,21,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Brick crease",     Armor, PeakCurve(3,23,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Diamond crease",   Armor, PeakCurve(3,24,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Telescope crease", Armor, PeakCurve(3,25,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gambler crease",   Armor, PeakCurve(12,25,25), [0,20], [PeakCurve(0,0,1), PeakCurve(0,0,10)]),
    )
