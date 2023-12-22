from enum import Enum
from indian import *
from typing import List, Optional
from player import *
from random import randint


class Turn(Enum):
    PLAYER = 0
    INDIAN = 1


class Game():
    def __init__(self) -> None:
        self.players: List[Player] = []
        self.bounty = 0
        self.turn = Turn.INDIAN
        self.in_fight = False

    def generate_indian(self) -> Indian:
        #Always get the cert avisé
        return Indian("cerf", "avisé", Gender.MALE, 30, 2, 5)

    def _change_turn(self) -> None:
        if self.turn == Turn.PLAYER:
            self.turn = Turn.INDIAN
        else:
            self.turn = Turn.PLAYER

    def fight(self) -> None:
        #First pass will change turn to the player
        #TODO create a fight object ?
        self._change_turn()
        player = self.players[randint(0, len(self.players) - 1)]
        indian = self.generate_indian()
        self._fight_between(player, indian)

    def _fight_between(self, player: Player, indian: Indian) -> None:

        if self.turn == Turn.PLAYER:
            player.hp -= indian.damage
        else:
            indian.hp -= player.damage

        if not indian.is_alive():
            #Finish the fight
            self.in_fight = False
            self.turn = Turn.INDIAN

    def add_player(self, name: str) -> None:
        self.players.append(Player(name))
