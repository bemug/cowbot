from enum import Enum
from aftermath import *
from indian import *
from typing import List, Optional
from player import *
from random import randint, choice


class Turn(Enum):
    PLAYER = 0
    INDIAN = 1


class Game():
    def __init__(self) -> None:
        self.players: List[Player] = []
        self.turn = Turn.INDIAN
        self.indian = None
        self.cash: int = 0

    def find_indian(self) -> None:
        #Always get the cerf avisé
        self.indian = Indian("cerf", "avisé", Gender.MALE, 30, 2, 5)

    def _change_turn(self) -> None:
        if self.turn == Turn.PLAYER:
            self.turn = Turn.INDIAN
        else:
            self.turn = Turn.PLAYER

    def start_fight(self) -> None:
        self.turn = choice(list(Turn))

    def process_fight(self) -> Aftermath:
        self._change_turn()
        player = self.players[randint(0, len(self.players) - 1)]
        if self.turn == Turn.PLAYER:
            source = player
            target = self.indian
        else:
            source = self.indian
            target = player
        from_hp: int = target.hp
        self._hit(source, target)
        return Aftermath(source, target, from_hp, target.hp)

    def _hit(self, source, target) -> None:
        dmg: int = source.damage
        target.hp = max(target.hp - dmg, 0)

    def is_fight_over(self) -> bool:
        return self.indian.is_dead()

    def add_player(self, name: str) -> None:
        self.players.append(Player(name))
