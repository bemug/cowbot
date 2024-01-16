from enum import Enum


class Gender(Enum):
    FEMALE = 0
    MALE = 1


class Indian:
    def __init__(self, name: str, adjective: str, gender: Gender, exp: int) -> None:
        self.name = name
        self.adjective = adjective
        self.gender = gender
        self.exp = exp
        self.hp = self.get_max_hp()

    def get_level(self) -> int:
        #Indian level up 5/4 faster than players
        return int((self.exp * 5/4) ** (1. / 3)) + 1

    def get_damage(self) -> int:
        return 2 + self.get_level()

    def get_max_hp(self) -> int:
        return 8 + self.get_level()

    def is_dead(self) -> bool:
        return self.hp <= 0

    def __str__(self):
        return self.name.capitalize() + " " + self.adjective.capitalize()
