from foe import *
from typing import List, Optional
from player import *
from weapon import *
from armor import *
from random import randint, choice, uniform, randrange, shuffle
from datetime import datetime, time, timedelta
from utils import *
from lootable import *


class Game():
    cash_divider = 10
    hour_open = time(9, 30)
    hour_close = time(16, 30)
    fight_timeout = timedelta(minutes=30)
    tick_heal = timedelta(minutes=15)
    speed = 1

    def __init__(self) -> None:
        self.players: List[Player] = []
        self.foes: List[Foe] = []
        self.opened = Game.is_open_hour()
        #TODO fight item ?
        self.fights_nb_per_day = 2
        self.fight_times = []
        self.heal_times = []
        self.schedule()
        self.loot = []
        self.fight_order = []
        self.fighter_id = -1
        self.last_save = datetime.now()

    def schedule(self) -> None:
        self.schedule_fights()
        self.schedule_heals()
        self.last_scheduled = datetime.now()

    def schedule_fights(self) -> None:
        now = datetime.now()
        today_open: datetime = datetime.combine(now, Game.hour_open)
        today_close: datetime = datetime.combine(now, Game.hour_close)
        #Cut opening times in fights_nb_per_day number of periods
        fights_nb = self.fights_nb_per_day * Game.speed
        time_period: deltatime = (today_close - today_open) / fights_nb
        #Schedule a fight at a random time in each period
        self.fight_times.clear()
        for i in range(0, fights_nb):
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
        tick_heal = Game.tick_heal / Game.speed
        heal_time = today_open + tick_heal
        self.heal_times.clear()
        while heal_time <= today_close:
            self.heal_times.append(heal_time)
            heal_time += tick_heal
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
        for player in self.players:
            if player.ingame:
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

    def find_foes(self) -> None:
        if sum([player.ingame for player in self.players]) <= 0:
            raise RuntimeError
        #TODO generate combined/split foes with 5% chance of appearance
        for player in self.players:
            if player.ingame:
                #TODO peakcurve
                noised_foe_exp = player.foe_exp * uniform(0.8, 1.2)
                foe: Foe = Foe(noised_foe_exp)
                self.foes.append(foe)
                trace(f"Player {player} : add {str(foe)} level {str(foe.level)} with {str(noised_foe_exp)} exp")
            else:
                trace(f"Player {player} is not ingame, skipping")

    def start_fight(self) -> None:
        self.find_foes()
        self.fight_order = self.players + self.foes
        shuffle(self.fight_order)
        trace(f"Fight order: " + ", ".join(str(fighter) for fighter in self.fight_order))
        self.fighter_id = -1 #First process fight call will make it 0

    def process_fight(self) -> Aftermath:
        self.fighter_id = (self.fighter_id + 1) % len(self.fight_order)
        source = self.fight_order[self.fighter_id]
        if isinstance(source, Player):
            target_list = self.foes
        else:
            target_list = self.players
        #TODO have higher chance to pick someone at your level
        target = target_list[randint(0, len(target_list) - 1)]
        return source.hit(target)

    def exp_to_cash(exp: int):
        return int(exp / Game.cash_divider)

    def give_exp(self) -> int:
        total_exp: int = sum(foe.get_kill_exp() for foe in self.foes)
        exp: int = int(total_exp / len(self.players))
        if self.are_they_dead(self.foes):
            for player in self.players:
                trace("Added " + str(exp) + " to 'exp' and 'foe_exp' for " + str(player))
                player.add_exp(exp)
                player.foe_exp += exp
        else:
            for player in self.players:
                trace("Substracting " + str(exp) + " 'foe_exp' to " + str(player))
                player.foe_exp -= exp
            total_exp *= -1
        return Game.exp_to_cash(total_exp)

    def generate_loot(self) -> None:
        self.loot = []
        for foe in self.foes:
            trace(f"Generating loot from {foe}")
            for lootable in lootables:
                item = lootable.generate_item(foe.level)
                if item != None:
                    self.loot.append(item)

    def end_fight(self) -> int:
        self.generate_loot()
        return self.give_exp()

    def clean_after_fight(self):
        self.foes = []
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
        return self.are_they_dead(self.foes) or self.are_they_dead(self.players)

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

    def load():
        try:
            game = load_save("game")
            trace(f"Last game save was at {str(game.last_save)}")
            #We have no idea when the save will be loaded
            game.opened = Game.is_open_hour()
            #Kick out all players
            for player in game.players:
                player.ingame = False
            #If fights or heal were yesterday, reschedule
            fmt = "%Y-%m-%d"
            if datetime.now().strftime(fmt) != game.last_scheduled.strftime(fmt):
                trace("Save file belongs to yesterday or older, schedule new events and heal players")
                game.schedule()
                for player in game.players:
                    player.hp = player.get_max_hp()
        except (FileNotFoundError, IndexError):
            trace("No saves found, creating a new game")
            game = Game()
        return game

    def save(game):
        game.last_save = datetime.now()
        save_save(game, "game")
