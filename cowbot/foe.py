from enum import Enum
from random import choice

from cowbot.character import *


class Foe(Character):
    animals_file: str = "data/animals.txt"
    adjectives_file: str = "data/adjectives.txt"
    #Foe level up faster than players
    scale_factor = 4/5

    def __init__(self, exp: int) -> None:
        super().__init__()
        self.name = choice(open(Foe.animals_file).readlines()).strip() + \
                " " + \
                choice(open(Foe.adjectives_file).readlines()).strip()
        self.base_hp = 10
        self.base_damage = 4
        self.add_exp(exp)
        self.hp = self.get_max_hp() #After add_exp

    def get_kill_exp(self) -> int:
        return self.level * Character.exp_multiplier
