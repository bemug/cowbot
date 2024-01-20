from enum import Enum
from random import choice
from character import *


class Indian(Character):
    animals_file: str = "data/animals.txt"
    adjectives_file: str = "data/adjectives.txt"

    def __init__(self, exp: int) -> None:
        self.name = choice(open(Indian.animals_file).readlines()).strip()
        self.adjective = choice(open(Indian.adjectives_file).readlines()).strip()
        self.exp = exp
        self.hp = self.get_max_hp()

    def get_level(self) -> int:
        #Indian level up 5/4 faster than players
        return int((self.exp * 5/4) ** (1. / 3))

    def get_damage(self) -> int:
        return 2 + self.get_level()

    def get_max_hp(self) -> int:
        return 8 + self.get_level()

    def __str__(self):
        return self.name.capitalize() + " " + self.adjective.capitalize()
