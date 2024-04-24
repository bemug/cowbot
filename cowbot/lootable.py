from cowbot.peakcurve import *
from cowbot.downcurve import *
from cowbot.weapon import *
from cowbot.armor import *
from cowbot.consumable import *


class Lootable():

    loot_rate = 0.66

    def __init__(self, name, type, loot_chance, attr_list, attr_chance):
        self.name = name
        self.type = type
        loot_chance.peak_value *= Lootable.loot_rate
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
            attr1 += int(self.attr_chance[0].draw_center())
            try:
                attr2 += int(self.attr_chance[1].draw_center())
            except IndexError:
                pass
            if self.type == Consumable:
                return self.type(self.name, attr1)
            return self.type(self.name, attr1, attr2)

    def __str__(self) -> str:
        return self.name


lootables = (
        #Weapons
        #Must always loot at level 2
        Lootable("Pistolet de poche Derringer", Weapon, PeakCurve(2,2,5, 1/Lootable.loot_rate), [1], [DownCurve(5)]),
        Lootable("Revolver Colt",               Weapon, PeakCurve(2,10,15),      [2],     [DownCurve(7)]),
        Lootable("Revolver Remington",          Weapon, PeakCurve(2,11,15),      [1,4],   [DownCurve(7),  DownCurve(10)]),
        Lootable("Revolver S&W",                Weapon, PeakCurve(8,16,20),      [4],     [DownCurve(10)]),
        Lootable("Pistolet Volcanic",           Weapon, PeakCurve(8,17,20),      [2,9],   [DownCurve(10), DownCurve(10)]),
        Lootable("Fusil Spencer",               Weapon, PeakCurve(12,18,20),     [5,0],   [DownCurve(15), DownCurve(15)]),
        Lootable("Fusil Sharps",                Weapon, PeakCurve(14,21,22),     [3,14],  [DownCurve(15), DownCurve(15)]),
        Lootable("Fusil Springfield",           Weapon, PeakCurve(19,21,23),     [9,4],   [DownCurve(20), DownCurve(20)]),
        Lootable("Carabine Mauser",             Weapon, PeakCurve(20,23,24),     [4,19],  [DownCurve(20), DownCurve(20)]),
        Lootable("Carabine Winchester",         Weapon, PeakCurve(23,25,25),     [14,9],  [DownCurve(25), DownCurve(25)]),
        Lootable("Mitrailleuse Gatling",        Weapon, PeakCurve(10,25,25,0.1), [0,40],  [DownCurve(1),  DownCurve(30)]),
        ### Armors
        #Require at least level 4 to spawn
        Lootable("Chapeau Cattleman", Armor, PeakCurve(4,4,7),        [1],    [DownCurve(4)]),
        Lootable("Chapeau Bullrider", Armor, PeakCurve(4,11,15),      [3],    [DownCurve(6)]),
        Lootable("Chapeau Cutter",    Armor, PeakCurve(4,12,15),      [2,3],  [DownCurve(6),  DownCurve(6)]),
        Lootable("Chapeau Ridgetop",  Armor, PeakCurve(9,16,20),      [5],    [DownCurve(8)]),
        Lootable("Chapeau Dakota",    Armor, PeakCurve(9,17,20),      [3,6],  [DownCurve(8),  DownCurve(8)]),
        Lootable("Chapeau Montana",   Armor, PeakCurve(13,19,21),     [6,0],  [DownCurve(11), DownCurve(11)]),
        Lootable("Chapeau Gus",       Armor, PeakCurve(15,21,23),     [4,8],  [DownCurve(11), DownCurve(11)]),
        Lootable("Chapeau Brick",     Armor, PeakCurve(18,23,24),     [10,4], [DownCurve(13), DownCurve(13)]),
        Lootable("Chapeau Diamond",   Armor, PeakCurve(19,24,25),     [5,11], [DownCurve(13), DownCurve(13)]),
        Lootable("Chapeau Telescope", Armor, PeakCurve(22,25,25),     [15,6], [DownCurve(18), DownCurve(18)]),
        Lootable("Chapeau Gambler",   Armor, PeakCurve(12,25,25,0.1), [0,20], [DownCurve(1),  DownCurve(20)]),

        ### Consumables
        Lootable("Tequila", Consumable, PeakCurve(5,10,13,0.55),  [3],  [DownCurve(6)]),
        Lootable("Whisky",   Consumable, PeakCurve(10,15,18,0.7),  [9],  [DownCurve(6)]),
        Lootable("Rhum",     Consumable, PeakCurve(15,20,25,0.85), [15], [DownCurve(6)]),
        Lootable("Bière",    Consumable, PeakCurve(23,25,40,1),    [21], [DownCurve(6)]),
    )
