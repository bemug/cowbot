from enum import Enum


class Gender(Enum):
    FEMALE = 0
    MALE = 1


class Indian:
    def __init__(self, name: str, adjective: str, gender: Gender, hp: int,
                 damage: int, bounty: int) -> None:
        self.name = name
        self.adjective = adjective
        self.gender = gender
        self.hp = hp
        self.damage = damage
        self.bounty = bounty

    def indef_article(self) -> str:
       if self.gender == Gender.FEMALE:
           return "le"
       return "la"

    def def_article(self) -> str:
       if self.gender == Gender.FEMALE:
           return "le"
       return "la"

    def is_alive(self) -> bool:
        return self.hp > 0
