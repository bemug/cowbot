import re

from typing import List, Optional
from random import randint, choice, uniform, randrange, shuffle, random
from datetime import datetime, time, timedelta

from cowbot.foe import *
from cowbot.player import *
from cowbot.weapon import *
from cowbot.armor import *
from cowbot.consumable import *
from cowbot.utils import *
from cowbot.lootable import *


class Game():
    cash_divider = 10
    hour_open = time(9, 30)
    hour_close = time(16, 30)
    fight_timeout = timedelta(minutes=30)
    heal_timeout = timedelta(minutes=10)
    tick_heal = timedelta(minutes=15)
    foe_items_tries = 3
    foe_win_exp_multiplier = 3
    miss_rival_chance = 0.1
    speed = 1

    def __init__(self) -> None:
        self.players: List[Player] = []
        self.players_ingame: List[Player] = []
        self.foes: List[Foe] = []
        self.opened = Game.is_open_hour()
        #TODO fight item ?
        self.fights_nb_per_day = 2
        self.fight_times = []
        self.heal_times = []
        self.schedule()
        self.loot = {}
        self.loot_index = 0
        self.fight_order = []
        self.rivals = {}
        self.current_fighter = None
        self.last_save = datetime.now()
        self.total_fights = 0
        self.total_wins = 0

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
                if now - heal_time > Game.heal_timeout:
                    #Don't trace on purpose, this is to avoid spam on reload
                    continue
                trace("Heal " + str(heal_time))
                return True
        return False

    def heal_players(self, hp: int = 1) -> None:
        for player in self.players_ingame:
            player.heal(hp)

    def is_open_hour():
        weekno = datetime.today().weekday()
        if weekno >= 5:
            return False
        now = datetime.now()
        today_open: datetime = datetime.combine(now, Game.hour_open)
        today_close: datetime = datetime.combine(now, Game.hour_close)
        return now > today_open and now < today_close

    #TODO remove and replace by time compare with hour_open and hour_close
    def open(self):
        self.schedule()
        self.opened = True

    def close(self):
        self.opened = False

    def get_cash(self) -> int:
        return int(sum([player.foe_exp for player in self.players]) / Game.cash_divider)

    def find_foes(self) -> None:
        if len(self.players_ingame) <= 0:
            raise RuntimeError
        #TODO generate combined/split foes with 5% chance of appearance
        for player in self.players_ingame:
            foe_curve = PeakCurve(int(player.foe_exp * 0.6), player.foe_exp, int(player.foe_exp * 1.4))
            noised_foe_exp = int(player.foe_exp + foe_curve.draw())
            foe: Foe = Foe(noised_foe_exp)
            #Let the foe pick some items
            for i in range(0, Game.foe_items_tries):
                for lootable in lootables:
                    #If the player just reached level X, he didn't have the opportunity to get a loot for level X.
                    #The foe could be really deadly if he gets lucky.
                    #Make the foe only pick up items from its previous level, he'll catch up eventually.
                    item = lootable.generate_item(foe.level - 1)
                    if item != None:
                        if isinstance(item, Weapon) and foe.weapon == None:
                            foe.weapon = item
                        elif isinstance(item, Armor) and foe.armor == None:
                            foe.armor = item
                        if foe.weapon != None and foe.armor != None:
                            break
            self.foes.append(foe)
            self.rivals[player] = foe
            self.rivals[foe] = player
            trace(f"Player {player} : add {str(foe)} level {str(foe.level)} ({str(noised_foe_exp)} xp) with '{foe.weapon}' and '{foe.armor}'")

    def start_fight(self) -> None:
        self.find_foes()
        self.fight_order = self.players_ingame + self.foes
        shuffle(self.fight_order)
        trace(f"Fight order: " + ", ".join(str(fighter) for fighter in self.fight_order))
        self.current_fighter = self.fight_order[-1] #First process fight call will make it the first fighter

    def find_new_rival(self, old_rival):
        if isinstance(old_rival, Player):
            target_list = self.players_ingame
            source_list = self.foes
        else:
            target_list = self.foes
            source_list = self.players_ingame
        for source in source_list:
            if self.rivals[source] == old_rival:
                next_rival = None
                for target in target_list:
                    if not target.is_dead():
                        if next_rival == None or abs(source.level - target.level) < abs(source.level - next_rival.level):
                            next_rival = target
                trace(f"Switch {source} rival to {next_rival}")
                self.rivals[source] = next_rival

    def process_fight(self) -> Aftermath:
        current_fighter_id = self.fight_order.index(self.current_fighter)
        self.current_fighter = self.fight_order[(current_fighter_id + 1) % len(self.fight_order)]
        source = self.current_fighter
        if random() < Game.miss_rival_chance:
            target = source
            while target == source:
                target = choice(self.fight_order) #This is a feature
            trace(f"Hit from {source} ignores rival, choose {target} instead")
        else:
            target = self.rivals[source]
        aftermath = source.hit(target, self.rivals[source])
        if target.is_dead():
            self.fight_order.remove(target)
            self.rivals[target] = None #Just in case
            self.find_new_rival(target)
        return aftermath

    def exp_to_cash(exp: int):
        return int(exp / Game.cash_divider)

    def handle_exp(self) -> int:
        total_exp: int = sum(foe.get_kill_exp() for foe in self.foes)
        exp: int = int(total_exp / len(self.players_ingame))
        if self.has_lost(self.foes):
            for player in self.players_ingame:
                trace("Add " + str(exp) + " to 'exp' and 'foe_exp' for " + str(player))
                player.add_exp(exp)
                player.foe_exp += exp
        else:
            exp *= Game.foe_win_exp_multiplier
            total_exp *= Game.foe_win_exp_multiplier * -1
            for player in self.players_ingame:
                trace("Substract " + str(exp) + " 'foe_exp' to " + str(player))
                player.foe_exp = max(player.foe_exp - exp, 0)
        return Game.exp_to_cash(total_exp)

    def generate_loot(self) -> None:
        for foe in self.foes:
            trace(f"Generating loot from {foe}")
            for lootable in lootables:
                item = lootable.generate_item(foe.level)
                if item != None:
                    self.loot[self.loot_index] = item
                    self.loot_index += 1

    def end_fight(self) -> int:
        self.loot_index = 0
        self.loot.clear()
        self.total_fights += 1
        if self.has_lost(self.foes):
            self.generate_loot()
            self.total_wins += 1
        return self.handle_exp()

    def clean_after_fight(self):
        self.foes = []
        self.rivals = {}
        for player in self.players_ingame:
            if player.hp <= 0:
                trace("Set " + str(player) + " to 1 hp")
                player.hp = 1

    def has_lost(self, list) -> bool:
        for elem in list:
            if not elem.is_dead():
                return False
        return True

    def is_fight_over(self) -> bool:
        return self.has_lost(self.foes) or self.has_lost(self.players_ingame)

    def find_player(self, name: str, create: bool = False) -> Player:
        #Remove spurious '_'
        name = re.sub('_*$', '', name)
        player : Player = next((player for player in self.players if player.name == name), None)
        if not player and create:
            trace(f"Player {name} not found, adding to players list")
            player: Player = Player(name)
            self.players.append(player)
        return player

    def do_pick(self, player: Player, loot_index: int) -> [int, Item] :
        if len(player.inventory) > Player.inventory_size:
            raise ValueError
        item = self.loot[loot_index]
        del self.loot[loot_index]
        slot = player.next_slot()
        player.inventory[slot] = item
        trace(f"Pick : {self.loot}")
        trace(f"{player} inventory : {player.inventory}")
        return [slot, item]

    def do_drop(self, player: Player, loot_index: int) -> [int, Item, bool] :
        unequipped: bool = False
        item = player.inventory[loot_index]
        #Check if object is equipped, and if it is, unequip it
        if player.weapon == item:
            trace(f"Removing {item} as equipped weapon")
            player.weapon = None
            unequipped = True
        if player.armor == item:
            trace(f"Removing {item} as equipped armor")
            player.armor = None
            unequipped = True
        del player.inventory[loot_index]
        slot = self.loot_index
        self.loot[slot] = item
        self.loot_index += 1
        trace(f"Loot : {self.loot}")
        trace(f"{player} inventory : {player.inventory}")
        return [slot, item, unequipped]

    def do_equip(self, player: Player, loot_index: int) -> [Item, Item] :
        item = player.inventory[loot_index]
        if isinstance(item, Weapon):
            old_item = player.weapon
            player.weapon = item
            return [old_item, item]
        elif isinstance(item, Armor):
            old_item = player.armor
            player.armor = item
            return [old_item, item]
        raise ValueError

    def do_drink(self, player: Player, loot_index: int) -> Item :
        item = player.inventory[loot_index]
        if isinstance(item, Consumable):
            player.heal(item.heal)
            del player.inventory[loot_index]
            return item
        raise ValueError

    def load():
        try:
            game = load_save("game")
            trace(f"Last game save was at {str(game.last_save)}")
            #We have no idea when the save will be loaded
            game.opened = Game.is_open_hour()
            #Kick out all players
            game.players_ingame.clear()
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
