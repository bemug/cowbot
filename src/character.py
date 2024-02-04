from aftermath import *
from random import random

class Character:
    level_up_speed = 4
    exp_multiplier = 100
    crit_multiplier = 1.5
    miss_multiplier = 0

    def __init__(self):
        self.level = 1
        self.exp = 0
        self.weapon = None
        self.armor = None

    def __str__(self):
        return self.name.capitalize()

    def no_hl_str(self) -> str:
        #Insert this 0 width whitespace to avoid highlighting people: ​
        #See https://blanktext.net/
        s: str = self.__str__()
        return s[:1] + '​' + s[1:]

    def get_damage(self) -> int:
        return self.base_damage + self.level - 1

    def get_max_hp(self) -> int:
        return self.base_hp + self.level - 1

    def is_dead(self):
        return self.hp <= 0

    def get_max_exp(self) -> int:
        return int(pow((self.level + 1), 3) / Character.level_up_speed * self.__class__.scale_factor * Character.exp_multiplier)

    def add_exp(self, xp: int) -> int:
        old_level: int = self.level
        self.exp += xp
        while self.exp >= self.get_max_exp():
            self.exp -= self.get_max_exp()
            self.level += 1
        return self.level - old_level

    def has_equipped(self, item):
        return self.weapon == item or self.armor == item

    def hit(self, target):
        base_dmg: int = self.get_damage()
        weapon_dmg = self.weapon.dmg if self.weapon else 0
        total_dmg = base_dmg + weapon_dmg
        armor = self.armor.arm if self.armor != None else 0
        armor = self.armor.arm if self.armor != None else 0
        crit = 1
        miss = 1
        if self.weapon and random() < (self.weapon.crit / 100):
            crit = Character.crit_multiplier
        if self.armor and random() < (self.armor.miss / 100):
            miss = Character.miss_multiplier
        hit: int = int(((base_dmg + weapon_dmg) * crit - armor) * miss)
        target.hp = int(max(target.hp - hit, 0))
        return Aftermath(self, target, total_dmg, armor, crit, miss, hit)
