from random import randint
from monster import *
from player import *

class Turn(Enum):
    PLAYER = 0,
    MONSTER = 1,

class Dungeon():

    def __init__(self):
        self.players = []
        self.player = None
        self.bounty = 0
        self.monster = None
        self.turn = Turn.MONSTER
        self.in_fight = False

    def generate_monster(self):
        #Always get the rat
        self.monster = Monster("rat", "d'égout", Gender.MALE, 30, 2, 5)

    def _change_turn(self):
        if self.turn == Turn.PLAYER:
            self.turn = Turn.MONSTER
        else:
            self.turn = Turn.PLAYER

    def fight(self):
        #First pass will change turn to the player
        self._change_turn()

        self.player = self.players[randint(0, len(self.players) - 1)]

        if self.turn == Turn.PLAYER:
            self.player.hp -= self.monster.damage
        else:
            self.monster.hp -= self.player.damage

        if not self.monster.is_alive():
            #Finish the fight
            self.in_fight = False
            self.turn = Turn.MONSTER

    def clear_monster(self):
        self.monster = None

    def add_player(self, name):
        self.players.append(Player(name))
