from enum import Enum
from aftermath import *
from indian import *
from typing import List, Optional
from player import *
from random import randint, choice, uniform


class Turn(Enum):
    PLAYER = 0
    INDIAN = 1


class Game():
    def __init__(self) -> None:
        self.players: List[Player] = []
        self.indians: List[Indian] = []
        self.turn = Turn.PLAYER

    def find_indians(self) -> None:
        #TODO generate combined/split indians with 5% chance of appearance
        for player in self.players:
            noised_foe_exp = player.foe_exp * uniform(0.8, 1.2)
            self.indians.append(Indian("cerf", "avisé", Gender.MALE, noised_foe_exp))
            #self.indians.append(Indian("renard", "apprivoisé", Gender.MALE, noised_foe_exp))
            #self.indians.append(Indian("loutre", "malade", Gender.MALE, noised_foe_exp))

    def _change_turn(self) -> None:
        if self.turn == Turn.PLAYER:
            self.turn = Turn.INDIAN
        else:
            self.turn = Turn.PLAYER

    def start_fight(self) -> None:
        #Randomize first turn
        self.turn = choice(list(Turn))
        self.find_indians()

    def process_fight(self) -> Aftermath:
        self._change_turn()
        player = self.players[randint(0, len(self.players) - 1)]
        indian = self.indians[randint(0, len(self.indians) - 1)]
        if self.turn == Turn.PLAYER:
            source = player
            target = indian
        else:
            source = indian
            target = player
        from_hp: int = target.hp
        self._hit(source, target)
        return Aftermath(source, target, from_hp, target.hp)

    def _hit(self, source, target) -> None:
        dmg: int = source._get_damage()
        target.hp = max(target.hp - dmg, 0)

    def are_they_dead(self, list) -> bool:
        for elem in list:
            if not elem.is_dead():
                return False
        return True

    def is_fight_over(self) -> bool:
        return self.are_they_dead(self.indians) or self.are_they_dead(self.players)

    def add_player(self, name: str) -> None:
        self.players.append(Player(name))
