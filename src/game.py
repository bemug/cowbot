from enum import Enum
from aftermath import *
from indian import *
from typing import List, Optional
from player import *
from weapon import *
from armor import *
from random import randint, choice, uniform, randrange
from datetime import datetime, time, timedelta
from utils import *


class Turn(Enum):
    PLAYER = 0
    INDIAN = 1


class Game():
    cash_divider = 10
    hour_open = time(9, 30)
    hour_close = time(16, 30)
    fight_timeout = timedelta(minutes=30)
    tick_heal = timedelta(minutes=15)

    def __init__(self) -> None:
        self.players: List[Player] = []
        self.indians: List[Indian] = []
        self.turn = Turn.PLAYER
        self.opened = Game.is_open_hour()
        #TODO fight item ?
        self.fights_nb_per_day = 2
        self.fight_times = []
        self.schedule_fights() #TODO should remove once loading is done if bot is reloaded today
        self.heal_times = []
        self.schedule_heals() #TODO same as above
        self.loot = []

    def schedule_fights(self) -> None:
        now = datetime.now()
        today_open: datetime = datetime.combine(now, Game.hour_open)
        today_close: datetime = datetime.combine(now, Game.hour_close)
        #Cut opening times in fights_nb_per_day number of periods
        time_period: deltatime = (today_close - today_open) / self.fights_nb_per_day
        #Schedule a fight at a random time in each period
        self.fight_times.clear()
        for i in range(0, self.fights_nb_per_day):
            start: timestamp = (today_open + i * time_period).timestamp()
            end: timestamp = (today_open + (i + 1) * time_period).timestamp()
            self.fight_times.append(datetime.fromtimestamp(randrange(start, end)))
        trace("Scheduled fights: " + '; '.join(str(fight) for fight in self.fight_times))

    def is_fight_time(self) -> bool:
        now = datetime.now()
        #Iterate over a copy so we can remove items safely
        for fight_time in self.fight_times[:]:
            if now > fight_time: #TODO use same reference of time, put 'now' in game
                self.fight_times.remove(fight_time)
                if now - fight_time > Game.fight_timeout:
                    trace("Discarding expired fight " + str(fight_time))
                    continue
                trace("Selecting fight " + str(fight_time))
                return True
        return False

    def schedule_heals(self):
        now = datetime.now()
        today_open: datetime = datetime.combine(now, Game.hour_open)
        today_close: datetime = datetime.combine(now, Game.hour_close)
        heal_time = today_open + Game.tick_heal
        self.heal_times.clear()
        while heal_time <= today_close:
            self.heal_times.append(heal_time)
            heal_time += Game.tick_heal
        trace("Scheduled heals: " + '; '.join(str(heal) for heal in self.heal_times))

    def is_heal_time(self) -> bool:
        now = datetime.now()
        #Iterate over a copy so we can remove items safely
        for heal_time in self.heal_times[:]:
            if now > heal_time:
                self.heal_times.remove(heal_time)
                #Don't discard aything, we want the player to receive its missing health even if we miss a fight inbetween.
                #That's a compensation incase the game crashed.
                trace("Heal " + str(heal_time))
                return True
        return False

    def heal_players(self, hp: int = 1) -> None:
        #TODO only players INSIDE the game
        for player in self.players:
            player.hp = min(player.hp + hp, player.get_max_hp())

    def is_open_hour():
        now = datetime.now()
        today_open: datetime = datetime.combine(now, Game.hour_open)
        today_close: datetime = datetime.combine(now, Game.hour_close)
        return now > today_open and now < today_close

    #TODO remove and replace by time compare with hour_open and hour_close
    def open(self):
        self.schedule_fights()
        self.schedule_heals()
        self.opened = True

    def close(self):
        self.opened = False

    def get_cash(self) -> int:
        return int(sum([player.foe_exp for player in self.players]) / Game.cash_divider)

    def find_indians(self) -> None:
        if len(self.players) <= 0:
            raise RuntimeError
        #TODO generate combined/split indians with 5% chance of appearance
        for player in self.players:
            noised_foe_exp = player.foe_exp * uniform(0.8, 1.2)
            indian: Indian = Indian(noised_foe_exp)
            trace("Adding " + str(indian) + " foe level " + str(indian.level) + " to fight with " + str(noised_foe_exp) + " exp")
            self.indians.append(indian)

    def _change_turn(self) -> None:
        if self.turn == Turn.PLAYER:
            self.turn = Turn.INDIAN
        else:
            self.turn = Turn.PLAYER

    def start_fight(self) -> None:
        #Randomize first turn
        self.find_indians()
        self.turn = choice(list(Turn))

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
        return source.hit(target)

    def exp_to_cash(exp: int):
        return int(exp / Game.cash_divider)

    def give_exp(self) -> int:
        total_exp: int = sum(indian.get_kill_exp() for indian in self.indians)
        exp: int = int(total_exp / len(self.players))
        if self.are_they_dead(self.indians):
            for player in self.players:
                trace("Add " + str(exp) + " for exp and foe_exp to " + str(player))
                player.add_exp(exp)
                player.foe_exp += exp
        else:
            for player in self.players:
                trace("Substracting " + str(exp) + " foe_exp to " + str(player))
                player.foe_exp -= exp
            total_exp *= -1
        return Game.exp_to_cash(total_exp)

    def generate_loot(self) -> None:
        self.loot = []
        self.loot.append(Weapon("Colt", 1, 50))
        self.loot.append(Armor("Stetson en laine", 1, 50))

    def end_fight(self) -> int:
        self.generate_loot()
        return self.give_exp()

    def clean_after_fight(self):
        self.indians = []
        for player in self.players:
            if player.hp <= 0:
                trace("Set " + str(player) + " to 1")
                player.hp = 1

    def are_they_dead(self, list) -> bool: #TODO rename "has_won" and change calls
        for elem in list:
            if not elem.is_dead():
                return False
        return True

    def is_fight_over(self) -> bool:
        return self.are_they_dead(self.indians) or self.are_they_dead(self.players)

    def find_player(self, name: str, create: bool = False) -> Player:
        player : Player = next((player for player in self.players if player.name == name), None)
        if not player and create:
            trace(f"Player {name} not found, adding to players list")
            player: Player = Player(name)
            self.players.append(player)
        return player

    def do_loot(self, player: Player, loot_index: int) -> Item :
        item = self.loot[loot_index]
        if item == None:
            raise IndexError
        append_in_none(player.inventory, item)
        replace_by_none(self.loot, item)
        trace(f"Loot : {self.loot}")
        trace(f"{player} inventory : {player.inventory}")
        return item

    def do_drop(self, player: Player, loot_index: int) -> [Item, bool] :
        unequipped: bool = False
        item = player.inventory[loot_index]
        if item == None:
            raise IndexError
        #Check if object is equipped, and if it is, unequip it
        if player.weapon == item:
            trace(f"Removing {item} as equipped weapon")
            player.weapon = None
            unequipped = True
        if player.armor == item:
            trace(f"Removing {item} as equipped armor")
            player.armor = None
            unequipped = True
        append_in_none(self.loot, item)
        replace_by_none(player.inventory, item)
        trace(f"Loot : {self.loot}")
        trace(f"{player} inventory : {player.inventory}")
        return item, unequipped

    def do_equip(self, player: Player, loot_index: int) -> Item :
        item = player.inventory[loot_index]
        if item == None:
            raise IndexError
        if isinstance(item, Weapon):
            player.weapon = item
            return item
        elif isinstance(item, Armor):
            player.armor = item
            return item
        raise ValueError
