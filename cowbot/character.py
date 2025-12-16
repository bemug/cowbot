from random import random

from cowbot.aftermath import *

class Character:
    level_up_speed = 10
    exp_multiplier = 100
    crit_multiplier = 1.5
    miss_multiplier = 0
    level_max = 25

    def __init__(self):
        self.level = 1
        self.exp = 0
        self.weapon = None
        self.armor = None

    def __str__(self):
        return self.name

    def no_hl_str(self) -> str:
        #Used to avoid highlighting people
        #Previously we used a 'zero width space' caracter, but it means the word is semantically separated in two
        #Use a 'word joiner' caracter instead to mark it as a single word, but still differ from the origin word : ⁠
        s: str = self.__str__()
        return s[:1] + '⁠' + s[1:]

    def get_damage(self) -> int:
        return self.base_damage + self.level - 1

    def get_max_hp(self) -> int:
        return self.base_hp + (self.level - 1) * 2

    def is_dead(self):
        return self.hp <= 0

    def get_max_exp(self, level=-1) -> int:
        if level == -1:
            level = self.level
        return int(pow((level + 1), 3) / Character.level_up_speed * self.__class__.scale_factor * Character.exp_multiplier)

    def add_exp(self, xp: int) -> int:
        old_level: int = self.level
        self.exp += xp
        while self.exp >= self.get_max_exp():
            self.exp -= self.get_max_exp()
            self.level += 1
        #Cap at max level
        if self.level >= Character.level_max:
            self.level = Character.level_max
            self.exp = self.get_max_exp(Character.level_max)
        return self.level - old_level

    def has_equipped(self, item):
        return self.weapon == item or self.armor == item

    def hit(self, target, rival):
        base_dmg: int = self.get_damage()
        weapon_dmg = self.weapon.damage if self.weapon != None else 0
        total_dmg = base_dmg + weapon_dmg
        armor = target.armor.armor if target.armor != None else 0
        crit = 1
        miss = 1
        if self.weapon and random() < (self.weapon.critical / 100):
            crit = Character.crit_multiplier
        if target.armor and random() < (target.armor.miss / 100):
            miss = Character.miss_multiplier
        hit: int = max(int((base_dmg + weapon_dmg) * crit) - armor, 0) * miss
        old_hp = target.hp
        target.hp = max(target.hp - hit, 0)
        return Aftermath(self, target, total_dmg, armor, crit, miss, hit, old_hp, rival)

    def heal(self, hp = 1):
        self.hp = min(self.hp + hp, self.get_max_hp())
