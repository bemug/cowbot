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

    def get_cash(self):
        return sum([player.foe_exp for player in self.players])


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
        #TODO instead of turn use a list with all people, and shuffle it at start
        self._change_turn()
        player = self.players[randint(0, len(self.players) - 1)]
        indian = self.indians[randint(0, len(self.indians) - 1)]
        if self.turn == Turn.PLAYER:
            source = player
            target = indian
        else:
            source = indian
            target = player
        damage = self._hit(source, target)
        return Aftermath(source, target, damage)

    def get_end_fight_xp(self) -> int:
        return int(pow(sum(indian.get_level() for indian in self.indians), 2) / len(self.players))

    def end_fight(self) -> int:
        delta_exp = self.get_end_fight_xp()
        for player in self.players:
            if self.are_they_dead(self.indians):
                player.exp += delta_exp
                player.foe_exp += delta_exp
                return delta_exp
            else:
                player.foe_exp -= delta_exp
                return delta_exp * -1

    def clean_after_fight(self):
        self.indians = []
        for player in self.players:
            if player.hp <= 0:
                player.hp = 1

    def _hit(self, source, target) -> int:
        dmg: int = source.get_damage()
        target.hp = max(target.hp - dmg, 0)
        return dmg

    def are_they_dead(self, list) -> bool: #TODO rename "did_win" and change calls
        for elem in list:
            if not elem.is_dead():
                return False
        return True

    def is_fight_over(self) -> bool:
        return self.are_they_dead(self.indians) or self.are_they_dead(self.players)

    def add_player(self, name: str) -> None:
        self.players.append(Player(name))
