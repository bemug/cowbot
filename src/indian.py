from enum import Enum
from random import choice
from character import *


class Indian(Character):
    animals_file: str = "data/animals.txt"
    adjectives_file: str = "data/adjectives.txt"
    #Indian level up faster than players
    scale_factor = 4/5

    def __init__(self, exp: int) -> None:
        super().__init__()
        self.name = choice(open(Indian.animals_file).readlines()).strip() + \
                " " + \
                choice(open(Indian.adjectives_file).readlines()).strip()
        self.base_hp = 8
        self.hp = self.get_max_hp()
        self.base_damage = 2
        self.add_exp(exp)

    def get_kill_exp(self) -> int:
        return self.level * Character.exp_multiplier
