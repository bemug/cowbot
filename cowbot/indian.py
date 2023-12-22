from enum import Enum


class Gender(Enum):
    FEMALE = 0,
    MALE = 1,
    

class Monster:

    def __init__(self, name, adjective, gender, hp, damage, bounty):
        self.name = name
        self.adjective = adjective
        self.gender = gender,
        self.hp = hp
        self.damage = damage
        self.bounty = bounty
        
    def indef_article(self):
       if self.gender == Gender.FEMALE:
           return "le"
       return "la"

    def def_article(self):
       if self.gender == Gender.FEMALE:
           return "le"
       return "la"

    def is_alive(self):
        return self.hp > 0
