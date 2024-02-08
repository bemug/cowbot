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
        Lootable("Pistolet de poche Derringer", Weapon, PeakCurve(2,0,5), [1], [PeakCurve(0,0,3)]),
        Lootable("Revolver Colt", Weapon, PeakCurve(2,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Revolver Remington", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Revolver S&W", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Pistolet Volcanic", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Fusil Spencer", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Fusil Sharps", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Fusil Springfield", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Carabine Mauser", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Carabine Winchester", Weapon, PeakCurve(0,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Mitrailleuse Gatling", Weapon, PeakCurve(10,25,25,0.1), [0,40], [PeakCurve(0,0,1), PeakCurve(0,0,20)]),
        ### Armors
        #Require at least level 4 to spawn
        Lootable("Open crease", Weapon, PeakCurve(4,4,5), [1], [PeakCurve(0,0,3)]),
        Lootable("Cattleman crease", Weapon, PeakCurve(4,4,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Cutter crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Ridgetop crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Dakota crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Montana crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gus crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Brick crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Diamond crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Telescope crease", Weapon, PeakCurve(3,0,5), [1,0], [PeakCurve(0,0,3), PeakCurve(0,0,3)]),
        Lootable("Gambler crease", Weapon, PeakCurve(12,25,25), [0,20], [PeakCurve(0,0,1), PeakCurve(0,0,10)]),
    )
