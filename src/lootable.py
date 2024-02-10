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
            attr1 = self.attr_list[0]
            try:
                attr2 = self.attr_list[1]
            except IndexError:
                attr2 = 0
            attr1 += int(self.attr_chance[0].draw())
            try:
                attr2 += int(self.attr_chance[1].draw())
            except IndexError:
                pass
            return self.type(self.name, attr1, attr2)

    def __str__(self) -> str:
        return self.name


lootables = (
        #TODO TriangleCurve for attr chances
        #Weapons
        #Require at least level 2 to spawn
        Lootable("Pistolet de poche Derringer", Weapon, PeakCurve(2,2,5),        [1],     [PeakCurve(0,0,6)]),
        Lootable("Revolver Colt",               Weapon, PeakCurve(2,10,15),      [3],     [PeakCurve(0,0,10)]),
        Lootable("Revolver Remington",          Weapon, PeakCurve(2,11,15),      [2,5],   [PeakCurve(0,0,8),  PeakCurve(0,0,10)]),
        Lootable("Revolver S&W",                Weapon, PeakCurve(8,16,20),      [5],     [PeakCurve(0,0,6)]),
        Lootable("Pistolet Volcanic",           Weapon, PeakCurve(8,17,20),      [3,10],  [PeakCurve(0,0,10), PeakCurve(0,0,10)]),
        Lootable("Fusil Spencer",               Weapon, PeakCurve(14,20,22),     [6,0],   [PeakCurve(0,0,10), PeakCurve(0,0,10)]),
        Lootable("Fusil Sharps",                Weapon, PeakCurve(14,21,22),     [4,15],  [PeakCurve(0,0,15), PeakCurve(0,0,10)]),
        Lootable("Fusil Springfield",           Weapon, PeakCurve(20,22,24),     [10,5],  [PeakCurve(0,0,15), PeakCurve(0,0,10)]),
        Lootable("Carabine Mauser",             Weapon, PeakCurve(20,23,24),     [5,20],  [PeakCurve(0,0,15), PeakCurve(0,0,15)]),
        Lootable("Carabine Winchester",         Weapon, PeakCurve(23,25,25),     [15,10], [PeakCurve(0,0,20), PeakCurve(0,0,20)]),
        Lootable("Mitrailleuse Gatling",        Weapon, PeakCurve(10,25,25,0.1), [0,40],  [PeakCurve(0,0,1),  PeakCurve(0,0,20)]),
        ### Armors
        #Require at least level 4 to spawn
        Lootable("Open crease",      Armor, PeakCurve(4,4,7),        [1],    [PeakCurve(0,0,4)]),
        Lootable("Cattleman crease", Armor, PeakCurve(4,11,15),      [2],    [PeakCurve(0,0,8)]),
        Lootable("Cutter crease",    Armor, PeakCurve(4,12,15),      [1,2],  [PeakCurve(0,0,6),  PeakCurve(0,0,8)]),
        Lootable("Ridgetop crease",  Armor, PeakCurve(9,16,20),      [4],    [PeakCurve(0,0,4)]),
        Lootable("Dakota crease",    Armor, PeakCurve(9,17,20),      [2,5],  [PeakCurve(0,0,8),  PeakCurve(0,0,8)]),
        Lootable("Montana crease",   Armor, PeakCurve(15,20,22),     [5,0],  [PeakCurve(0,0,8),  PeakCurve(0,0,8)]),
        Lootable("Gus crease",       Armor, PeakCurve(15,21,23),     [3,7],  [PeakCurve(0,0,13), PeakCurve(0,0,8)]),
        Lootable("Brick crease",     Armor, PeakCurve(19,23,25),     [9,3],  [PeakCurve(0,0,13), PeakCurve(0,0,8)]),
        Lootable("Diamond crease",   Armor, PeakCurve(19,24,25),     [4,10], [PeakCurve(0,0,13), PeakCurve(0,0,13)]),
        Lootable("Telescope crease", Armor, PeakCurve(22,25,25),     [14,5], [PeakCurve(0,0,18), PeakCurve(0,0,18)]),
        Lootable("Gambler crease",   Armor, PeakCurve(12,25,25,0.1), [0,20], [PeakCurve(0,0,1),  PeakCurve(0,0,20)]),
    )
