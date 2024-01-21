from enum import Enum
from random import choice
from character import *


class Indian(Character):
    animals_file: str = "data/animals.txt"
    adjectives_file: str = "data/adjectives.txt"

    def __init__(self, exp: int) -> None:
        self.name = choice(open(Indian.animals_file).readlines()).strip() + \
                " " + \
                choice(open(Indian.adjectives_file).readlines()).strip()
        self.exp = exp
        self.base_hp = 8
        self.hp = self.get_max_hp()
        self.base_damage = 2

    def get_level(self) -> int:
        #Indian level up 5/4 faster than players
        return int((self.exp * 5/4) ** (1. / 3))
