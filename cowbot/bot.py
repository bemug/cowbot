import irc.bot #type: ignore

from time import sleep
from typing import Any, Callable, Coroutine
from datetime import datetime
from textwrap import wrap

from cowbot.aftermath import *
from cowbot.game import *
from cowbot.foe import *
from cowbot.utils import *
from cowbot.visibility import Visibility as v


class Command():
    #TODO replace first any with Bot
    def __init__(self, callback: Callable[[Any, Any, Any, Any], Coroutine[Any, Any, None]], visibility: v) -> None:
        self.callback = callback
        self.visibility = visibility

    def help_asked(args, expected_len):
        try:
            if len(args) not in expected_len or args[0] == "help":
                return True
        except IndexError:
            pass
        return False


class Bot(irc.bot.SingleServerIRCBot): #type: ignore
    fight_wait = 2
    msg_wait = 0.5
    after_fight_wait = timedelta(milliseconds=10)


    ### IRC callbacks ###

    def __init__(self, channel, nickname, realname, server, port=6667, password="", admin=""):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, realname)
        self.channel = channel
        self.game = Game.load()
        if self.game.speed > 1:
            Bot.fight_wait = 1
        self.last_fight_time = datetime.now()
        self.admin = admin

    def is_admin(self, nick):
        return nick == self.admin

    def msg(self, target, msg):
        #This lib is fucked up.
        #It could either let me know how much byte it sends in a message, or either wrap lines for me.
        #We could anticipate the total message length, but even that fails and cut our message. Could be a socket issue.
        #Classic IRC clients cut at 350, just do the same and don't bother too much.
        max_chars = 350
        for sub_msg in wrap(msg, max_chars):
            try:
                self.connection.privmsg(target, sub_msg)
                trace("Sent to " + target + ": \"" + sub_msg + "\"")
            except irc.client.MessageTooLong:
                trace("Message to " + target + " too long : " + sub_msg + "\", dropping")

    def get_users(self):
        users: List = list(self.channels.get(self.channel).users())
        users.remove(self.connection.nickname)
        return sorted(users)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    #Fired every ~3min on libera.chat
    def on_ping(self, c, e):
        #Comes is the irc server, our target is our channel
        self._process_time(c, e, self.channel)

    def on_join(self, c, e):
        source = e.source.nick
        #As we join the channel, do the same thing as if we're pinged
        if source == self._nickname:
            trace(f"Join '{self.channel}'")
            #TODO advertise ourself as a bot
        else:
            #Could be an alias, check its status
            for player in self.game.players_ingame:
                if get_real_nick(source) == player.name:
                    trace(f"Voice '{source}' as he is an alias of ingame '{player.name}'.")
                    self.voice(e.target, source)
                    break

    def on_endofnames(self, c, e):
        trace(f"Receive '{self.channel}' user list")
        self.clear_missing_players(self.channel)

    def on_mode(self, c, e):
        try:
            if e.arguments[0] == "+o" and e.arguments[1] == self._nickname:
                trace(f"Receive operator mode for '{self.channel}'")
                self.restore_voice_status(self.channel)
        except IndexError:
            pass

    def on_privmsg(self, c, e):
        #Talk to our source
        target = e.source.nick
        self._process_command(c, e, target)

    def on_pubmsg(self, c, e):
        self._process_command(c, e, e.target)

    def on_part(self, c, e):
        self.handle_quit(e.source.nick, e.target)
    def on_kick(self, c, e):
        self.handle_quit(e.source.nick, e.target)
    def on_quit(self, c, e):
        self.handle_quit(e.source.nick, e.target)


    ### Game FSM and display ###

    def handle_quit(self, source, target):
        player: Player = self.game.find_player(source)
        if not player:
            return
        for user in self.get_users():
            if get_real_nick(user) == player.name:
                trace(f"Player {player} has an alias in channel as '{user}', Don't remove him from game")
                return
        if player in self.game.players_ingame:
            trace(f"Player {player} quit, remove him from ingame")
            self.game.players_ingame.remove(player)
        else:
            trace(f"Player {player} quit, but was not ingame. Do nothing")
        #This is a game status change, save the game
        Game.save(self.game)

    def debug_start(self):
        pass

    def _process_time(self, c, e, target):
        fmt= "%Hh%M"
        #Check opening hours
        if not self.game.opened and Game.is_open_hour():
            trace("Opening game")
            self.game.open()
            self.msg(target, f"Il est {Game.hour_open.strftime(fmt)}, le saloon ouvre ses portes 🌅")
        #Check if a fight is available before closing, to not miss any fights
        if self.game.opened: #Skip missed fights on closed hours, and don't heal
            while self.game.is_heal_time():
                self.game.heal_players()
                Game.save(self.game)
            if self.game.is_fight_time():
                self._fight(target)
                Game.save(self.game)
        if self.game.opened and not Game.is_open_hour():
            self.game.close()
            trace("Closing game")
            #TODO today's earnings
            self.msg(target, f"Il est {Game.hour_close.strftime(fmt)}, le saloon ferme 🌠")

    def _process_command(self, c, e, target):
        message: str = e.arguments[0]
        if message == "!" or message == "!!":
            return
        if message.startswith("!!") and self.is_admin(e.source.nick):
            command_array = self.admin_commands
        elif message.startswith('!'):
            command_array = self.commands
        else:
            return
        now = datetime.now()
        if now - self.last_fight_time < Bot.after_fight_wait:
            remaining_time = self.last_fight_time + Bot.after_fight_wait - now
            trace(f"Dropped '{str(e.arguments)}' as received in wait time. Remaining '{remaining_time}'")
            return

        trace("Command received: " + str(e))
        command: str = message.split(' ')[0]
        args: str = None
        try:
            args: str = message.rstrip().split(' ')[1:]
        except IndexError:
            pass
        #Check one command matches our command list
        matches = []
        for item in command_array:
            if item.startswith(command):
                matches.append(item)
        if len(matches) == 0:
            self.msg(target, f"{ERR} Commande inconnue : '{command}'")
            return
        if len(matches) > 1:
            self.msg(target, f"{ERR} Plusieurs commandes correspondent à ta demande : " + " ".join(matches))
            return
        cmd_str = matches[0]
        cmd = command_array[matches[0]]

        #Check you have the right to sue this command here
        if target == self.channel and not cmd.visibility & v.PUBLIC:
            self.msg(target, f"{ERR} Tu ne peux pas utiliser la commande '{cmd_str}' en public.")
            return
        elif target != self.channel and not cmd.visibility & v.PRIVATE:
            self.msg(target, f"{ERR} Tu ne peux pas utiliser la commande '{cmd_str}' en privé.")
            return

        #Everything is ok, execute the command
        cmd.callback(self, target, e.source.nick, args)
        Game.save(self.game)

    def _fight(self, target) -> None:
        log: str = ""
        number_str: str = ""
        step: int = 1

        try:
            self.game.start_fight()
        except RuntimeError:
            self.msg(target, f"Les indiens rôdent dehors. Je ne peux pas défendre le saloon seul. Je l'ai barricadé en attendant, mais c'est pas bon pour les ventes. Vous devriez entrer pour me filer un coup de main.")
            return

        if len(self.game.foes) > 1:
            number_str = "nt"
        self.msg(target, f"{list_str(self.game.foes)} débarque{number_str} dans le saloon {list_str(self.game.players_ingame)} !")
        sleep(Bot.fight_wait)
        while not self.game.is_fight_over():
            #Fight
            am: Aftermath = self.game.process_fight()

            #Construct log
            log = f"{step}. {am.source.no_hl_str()}"
            if am.target != am.rival:
                log += f" {decor_str('manque sa cible', decorations['important'])}, et"
            if am.source.weapon:
                log += f" tire sur {am.target.no_hl_str()} : "
            else:
                log += f" frappe {am.target.no_hl_str()} à mains nues : "

            did_crit: bool = am.source.weapon and am.critical != 1
            did_miss: bool = am.source.armor and am.miss != 1

            formula = decor_str(str(am.damage), decorations["dmg"])
            if did_crit:
                formula += " × " + decor_str(str(am.critical), decorations["crit"], False)
            if am.armor > 0:
                formula += " - " + decor_str(str(am.armor), decorations["arm"])
            if did_miss:
                formula = "(" + formula + ") × " + decor_str(str(am.miss), decorations["miss"], False)
            formula += " = " + decor_str(str(am.hit), decorations["hp"])
            log += formula

            if did_crit or did_miss:
                log += ", avec "
            with_crit = None
            with_miss = None
            if did_crit:
                with_crit = decor_str(str(am.source.weapon.critical), decorations["crit"])
            if did_miss:
                with_miss = decor_str(str(am.target.armor.miss), decorations["miss"])
            log += " et ".join(filter(None, [with_crit, with_miss]))

            log += ". Reste {} → {}.".format(
                    decor_str(f"{am.old_hp}/{am.target.get_max_hp()}", decorations["hp"], False),
                    decor_str(f"{am.target.hp}/{am.target.get_max_hp()}", decorations["hp"]))

            self.msg(target, log)

            if am.target.is_dead():
                sleep(self.msg_wait)
                self.msg(target, f"{am.target} est à terre.")

            step += 1
            sleep(Bot.fight_wait)

        #Backup levels for display
        levels = [player.level for player in self.game.players]
        cash_change = self.game.end_fight()

        if cash_change > 0:
            log = "VICTOIRE. Pendant la bagarre j'ai vendu pour {} de boissons. J'ai placé cet argent dans le tiroir-caisse ({}).".format(
                    decor_str(str(cash_change), decorations["cash"]),
                    decor_str(str(self.game.get_cash()), decorations["cash"]),
                )
            if self.game.get_cash() >= self.game.max_cash:
                log += " C'est le montant le plus haut jamais atteint !"
            self.msg(target, log)
            sleep(Bot.fight_wait)

            for i, player in enumerate(self.game.players):
                if player.level != levels[i]:
                    log = "{} passe au {} ({}).".format(
                            player,
                            decor_str(f"niveau {player.level}", decorations["level"]),
                            decor_str(f"{player.exp}/{player.get_max_exp()}", decorations["exp"]),
                        )
                    self.msg(target, log)
                    sleep(Bot.fight_wait)
            self._show_party(target)
            sleep(Bot.fight_wait)
            self._show_loot(target)
        else:
            log = "DEFAITE. Avant de s'échapper {} vole{} {} dans le tiroir-caisse ({}).".format(
                    list_str(self.game.foes),
                    number_str,
                    decor_str(str(-cash_change), decorations["cash"]),
                    decor_str(str(self.game.get_cash()), decorations["cash"]),
                    number_str,
                )
            self.msg(target, log)
        self.game.clean_after_fight()
        #Start a time to ignore all new messages that came inbetween the fight sleeps
        self.last_fight_time = datetime.now()

    def _str_slot(self, slot = -1):
        if slot != -1:
            return f"[{decor_str(f'{slot}', decorations['slot'])}]"
        return ""

    def _str_item(self, item, slot = -1, equipped = False):
        if item == None:
            return None
        ret = ""
        if slot != -1:
            ret += self._str_slot(slot)
        if isinstance(item, Weapon):
            decor = [decorations["dmg"], decorations["crit"]]
            attr1 = item.damage
            attr2 = item.critical
        elif isinstance(item, Armor):
            decor = [decorations["arm"], decorations["miss"]]
            attr1 = item.armor
            attr2 = item.miss
        elif isinstance(item, Consumable):
            decor = [decorations["hp"]]
            attr1 = item.heal
            attr2 = 0
        else:
            trace("Unknown item type, ignoring.")
            return
        if equipped:
            ret += "[E]"
        ret += str(item) + " " + decor_str(str(attr1), decor[0])
        if attr2 > 0:
            ret += " " + decor_str(str(attr2), decor[1])
        return ret

    def _show_party(self, target):
        if len(self.game.players_ingame) == 0:
            self.msg(target, f"{ERR} Il n'y a aucun joueur dans le saloon.")
            return
        party = []
        for player in self.game.players_ingame:
            str_party = player.no_hl_str() + " " + decor_str(f"{player.hp}/{player.get_max_hp()}", decorations["hp"])
            party.append(str_party)
        msg = "Groupe : " + list_str(party) + "."
        self.msg(target, msg)

    def _show_loot(self, target):
        log = "Dépouille : "
        items_list = []
        for i, item in sorted(self.game.loot.items()):
            items_list.append(f"{self._str_item(item, i)}")
        items_log = list_str(items_list)
        if items_log == "":
            log += " Vide"
        self.msg(target, log + items_log + ".")

    def _parse_uint(self, target, str_index: str) -> int:
        try:
            index = int(str_index)
        except ValueError:
            self.msg(target, f"{ERR} '{str_index}' doit être un nombre.")
            raise ValueError
        if index < 0:
            self.msg(target, f"{ERR} '{str_index}' doit être positif.")
            raise ValueError
        return index

    def voice(self, target, nick):
        trace(f"Mode +v '{nick}'")
        self.connection.mode(target, f"+v {nick}")

    def devoice(self, target, nick):
        trace(f"Mode -v '{nick}'")
        self.connection.mode(target, f"-v {nick}")

    def clear_missing_players(self, target):
        trace("Clear missing players")
        users = self.get_users()
        #Remove people that left
        #Iterate over a copy so we can remove items safely
        for player in self.game.players_ingame[:]:
            found = False
            for user in users:
                if get_real_nick(user) == player.name:
                    found = True
                    break
            if not found:
                trace(f"Player '{player}' left before save reload, remove him from game")
                self.game.players_ingame.remove(player)

    def restore_voice_status(self, target):
        trace("Restore voice status")
        users = self.get_users()
        #Set back voice status to all players
        for user in users:
            voiced = False
            for player in self.game.players_ingame:
                if get_real_nick(user) == player.name:
                    self.voice(target, user)
                    voiced = True
            if not voiced:
                self.devoice(target, user)


    ### Player commands ###

    def _callback_help(self, target: int, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!help : Affiche l'aide")
            return
        msg = "Commandes : " + decor_str(' '.join(self.commands), decorations['cmd']) +"."
        self.msg(target, msg)
        sleep(self.msg_wait)
        msg = "Taper '!<command> help' pour en savoir plus. Il est possible de ne taper que le debut d'une commande. Certaines commandes sont également accessibles par message privé."
        self.msg(target, msg)

    def _callback_pitch(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!pitch : Raconte l'histoire du lieu")
            return
        self.msg(target, "Bienvenue dans mon saloon, étranger. Installez vous. J'ai là un excellent whisky, goûtez-le.")
        sleep(self.msg_wait)
        self.msg(target, "Dites, j'ai entendu dire que vous n'aimiez pas trop les indiens ? Ils me mènent la vie dure ces temps-ci. Ils débarquent dans mon saloon et piquent dans la caisse. Peut être que vous pourriez en dessouder quelques-uns pour moi ? Je saurais me montrer redevable.")
        sleep(self.msg_wait)
        self.msg(target, f"Vous devriez entrer, et attendre ici. Je les connais bien ils ne devraient pas tarder.")

    def _callback_enter(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!enter : Entre dans le saloon.")
            return
        player: Player = self.game.find_player(source, True)
        if not player in self.game.players_ingame:
            self.game.players_ingame.append(player)
            for user in self.get_users():
                if get_real_nick(user) == player.name:
                    self.voice(target, user)
        else:
            self.msg(target, f"{ERR} Tu es déjà dans le saloon.")

    def _callback_leave(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!leave : Quitte le saloon.")
            return
        player: Player = self.game.find_player(source, True)
        if player in self.game.players_ingame:
            self.game.players_ingame.remove(player)
            for user in self.get_users():
                if get_real_nick(user) == player.name:
                    self.devoice(target, user)
        else:
            self.msg(target, f"{ERR} Tu es déjà hors du saloon.")

    def _callback_status(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0,1]):
            self.msg(target, "!status [joueur] : Affiche ton statut ou celui d'un joueur.")
            return
        try:
            source = args[0]
            player: Player = self.game.find_player(source)
        except IndexError:
            player: Player = self.game.find_player(source, True)
        if not player:
            self.msg(target, f"{ERR} Le joueur '{source}' n'existe pas.")
            return
        damage = player.get_damage()
        if player.weapon != None and player.weapon.damage != 0:
            damage += player.weapon.damage
        msg: str = "Cowboy {} : {}".format(
                decor_str(f"niveau {player.level}", decorations["level"]),
                decor_str(f"{damage}", decorations["dmg"]))
        if player.weapon != None and player.weapon.damage != 0:
            msg += " " + decor_str(f"({player.get_damage()} + {player.weapon.damage})", decorations["dmg"], False)
        msg += ", {} et {}.".format(
                decor_str(f"{player.hp}/{player.get_max_hp()}", decorations["hp"]),
                decor_str(f"{player.exp}/{player.get_max_exp()}", decorations["exp"]))
        if player.weapon != None or player.armor != None:
            msg += " Equipé de " + " et ".join(filter(None, ([self._str_item(player.weapon, player.get_slot(player.weapon), True), self._str_item(player.armor, player.get_slot(player.armor), True)]))) + "."
        self.msg(target, msg)

    def _callback_party(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!party : Affiche la santé des joueurs présents dans le saloon")
            return
        self._show_party(target)

    def _callback_cash(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!cash : Affiche le contenu du tiroir-caisse.")
            return
        log: str = "Le contenu actuel du tiroir-caisse est de {}.".format(
            decor_str(str(self.game.get_cash()), decorations["cash"])
        )
        if self.game.get_cash() >= self.game.max_cash:
            log += " C'est le montant le plus haut jamais atteint."
        else:
            log += " Le montant le plus haut jamais atteint est de {}.".format(
                decor_str(str(self.game.max_cash), decorations["cash"])
            )
        self.msg(target, log)

    def _callback_inventory(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!inventory : Affiche ton inventaire.")
            return
        player: Player = self.game.find_player(source, True)
        log = f"Inventaire ({player.get_inventory_usage()}) : "
        items_list = []
        for i, item in sorted(player.inventory.items()):
            items_list.append(f"{self._str_item(item, i, player.has_equipped(item))}")
        items_log = list_str(items_list)
        if items_log == "":
            log += " Vide"
        self.msg(target, log + items_log + ".")

    def _callback_loot(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!loot : Affiche la dépouille")
            return
        self._show_loot(target)

    def _callback_pick(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!pick <slot> : Recupère l'objet du slot 'slot' de la dépouille pour le placer dans ton inventaire")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            slot, item = self.game.do_pick(player, index)
        except KeyError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet [{int(args[0])}] dans la dépouille.")
            return
        except ValueError:
            self.msg(target, f"{ERR} Ton inventaire est plein.")
            return
        self.msg(target, f"{self._str_item(item)} ramassé dans le slot {self._str_slot(slot)} de ton inventaire ({player.get_inventory_usage()}).")

    def _callback_drop(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!drop <slot> : Place l'objet du slot 'slot' de ton inventaire dans la dépouille")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            slot, item, unequipped = self.game.do_drop(player, index)
        except KeyError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet [{int(args[0])}] dans ton inventaire.")
            return
        str_unequipped = ""
        if unequipped:
            str_unequipped = f"d'abord {decor_str('déséquipé', decorations['important'])}, puis "
        self.msg(target, f"{self._str_item(item)} {str_unequipped}déposé dans le slot {self._str_slot(slot)} de la dépouille.")

    def _callback_equip(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!equip <slot> : Equipe l'objet du slot 'slot' de ton inventaire")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            old_item, item = self.game.do_equip(player, index)
        except KeyError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet numéro [{int(args[0])}] dans ton inventaire.")
            return
        except ValueError:
            self.msg(target, f"{ERR} Cet objet ne peut pas être équippé.")
            return
        if old_item == item:
            self.msg(target, f"{ERR} {self._str_item(item, index, True)} est déjà équipé.")
            return
        msg =  f"{self._str_item(item)} équipé"
        if old_item != None:
            old_slot = player.get_slot(old_item)
            msg += f" à la place de {self._str_item(old_item, old_slot)}"
        msg += "."
        self.msg(target, msg)

    def _callback_drink(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!drink <slot> : Bois l'objet du slot 'slot' de ton inventaire")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        old_hp = player.hp
        try:
            item = self.game.do_drink(player, index)
        except KeyError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet numéro [{int(args[0])}] dans ton inventaire.")
            return
        except ValueError:
            self.msg(target, f"{ERR} Cet object ne peut pas être bu.")
            return
        msg = f"{self._str_item(item)} bu. "
        msg += decor_str(f"{old_hp}/{player.get_max_hp()}", decorations["hp"], False) + " → "
        msg += decor_str(f"{player.hp}/{player.get_max_hp()}", decorations["hp"]) + "."
        self.msg(target, msg)

    def _callback_pack(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!pack : Tasse ton inventaire, éliminant les trous.")
            return
        player: Player = self.game.find_player(source, True)
        player.pack_inventory()
        self.msg(target, f"Inventaire tassé ({player.get_inventory_usage()}).")

    def _callback_swap(self, target, source, args: str) -> None:
        if Command.help_asked(args, [2]):
            self.msg(target, "!swap <slot 1> <slot 2> : Permute 2 objets de ton inventaire. Permet de déplacer un objet si un des 2 slots est vide.")
            return
        try:
            index1 = self._parse_uint(target, args[0])
        except ValueError:
            return
        try:
            index2 = self._parse_uint(target, args[1])
        except ValueError:
            return
        if index1 == index2:
            self.msg(target, f"{ERR} Les 2 objets doivent être différents.")
            return
        player: Player = self.game.find_player(source, True)
        try:
            player.swap_inventory(index1, index2)
        except ValueError:
            self.msg(target, f"{ERR} Les 2 slots {self._str_slot(index1)} et {self._str_slot(index2)} sont vides.")
            return
        try:
            str1 = self._str_item(player.inventory[index1])
        except KeyError:
            str1 = ""
        try:
            str2 = self._str_item(player.inventory[index2])
        except KeyError:
            str2 = ""
        if str1 == "":
            self.msg(target, f"{str2} déplacé vers {self._str_slot(index2)}.")
            return
        elif str2 == "":
            self.msg(target, f"{str1} déplacé vers {self._str_slot(index1)}.")
            return
        self.msg(target, f"{str1} et {str2} permutés.")

    def _callback_show(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!show <slot> : Affiche un objet de ton inventaire.")
            return
        player: Player = self.game.find_player(source, True)
        try:
            slot = self._parse_uint(target, args[0])
        except ValueError:
            return
        try:
            item = player.inventory[slot]
        except KeyError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet [{int(args[0])}] dans ton inventaire.")
            return
        self.msg(target, self._str_item(item, slot, player.has_equipped(item)))

    def _callback_version(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!version : Affiche la version du jeu")
            return
        self.msg(target, git_version())


    ### Admin commands ###

    def _callback_admin_help(self, target: int, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!!help : Affiche l'aide admin")
            return
        msg = "Commandes : "
        msg += decor_str(' '.join(self.admin_commands), decorations['cmd'])
        msg += "."
        self.msg(target, msg)

    def _callback_admin_fight(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!!fight : Déclenche instantanément un combat")
            return
        self._fight(target)

    def _callback_admin_heal(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0,1]):
            self.msg(target, "!!heal [joueur] : Soigne un joueur")
            return
        try:
            source = args[0]
        except IndexError:
            pass
        player: Player = self.game.find_player(source)
        if not player:
            self.msg(target, f"{ERR} Le joueur '{source}' n'existe pas.")
            return
        player.hp = player.get_max_hp()
        self.msg(target, "Joueur soigné.")

    def _callback_admin_level(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1,2]):
            self.msg(target, "!!level [level] [joueur] : Change le niveau d'un joueur")
            return
        try:
            source = args[1]
        except IndexError:
            pass
        player: Player = self.game.find_player(source)
        if not player:
            self.msg(target, f"{ERR} Le joueur '{source}' n'existe pas.")
            return
        try:
            player.level = self._parse_uint(target, args[0])
        except ValueError:
            return
        #Reset exp to avoid issues (in case of leveling down for instance)
        player.exp = 0
        self.msg(target, f"Joueur au niveau {player.level}.")

    def _callback_admin_exp(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1,2]):
            self.msg(target, "!!exp [level] [joueur] : Change l'expérience d'un joueur")
            return
        try:
            source = args[1]
        except IndexError:
            pass
        player: Player = self.game.find_player(source)
        if not player:
            self.msg(target, f"{ERR} Le joueur '{source}' n'existe pas.")
            return
        try:
            exp: int = self._parse_uint(target, args[0])
        except ValueError:
            return
        if exp > player.get_max_exp():
            self.msg(target, f"{ERR} L'experience de {player.no_hl_str()} ne peut dépasser {player.get_max_exp()} d'expérience.")
            return
        player.exp = exp
        self.msg(target, f"Experience du joueur {player.exp}.")

    def _callback_admin_say(self, target, source, args: str) -> None:
        # Treat all arguments as one
        args = list(filter(None, [' '.join(args)]))
        if Command.help_asked(args, [1]):
            self.msg(target, "!!say <message> : Parle")
            return
        self.msg(self.channel, ' '.join(args))

    def _callback_admin_out(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, f"!!out : Expulse tout le monde du saloon.")
            return
        if len(self.game.players_ingame) == 0:
            self.msg(self.channel, "Il n'y a personne dans le saloon actuellement.")
            return
        self.msg(self.channel, f"Aller hop, tout le monde dehors ! Vous êtes maintenant hors du saloon {list_str(self.game.players_ingame)}.")
        for player in self.game.players_ingame:
            self.connection.mode(target, f"-v {player}")
        self.game.players_ingame.clear()

    ### Commands lists ###

    commands = {
        "!help": Command(_callback_help, v.PUBLIC | v.PRIVATE),
        "!pitch": Command(_callback_pitch, v.PUBLIC | v.PRIVATE),
        "!enter": Command(_callback_enter, v.PUBLIC),
        "!leave": Command(_callback_leave, v.PUBLIC),
        "!cash": Command(_callback_cash, v.PUBLIC | v.PRIVATE),
        "!party": Command(_callback_party, v.PUBLIC | v.PRIVATE),
        "!status": Command(_callback_status, v.PUBLIC | v.PRIVATE),
        "!inventory": Command(_callback_inventory, v.PUBLIC | v.PRIVATE),
        "!loot": Command(_callback_loot, v.PUBLIC | v.PRIVATE),
        "!pick": Command(_callback_pick, v.PUBLIC),
        "!drop": Command(_callback_drop, v.PUBLIC),
        "!equip": Command(_callback_equip, v.PUBLIC),
        "!drink": Command(_callback_drink, v.PUBLIC | v.PRIVATE),
        "!pack": Command(_callback_pack, v.PUBLIC | v.PRIVATE),
        "!swap": Command(_callback_swap, v.PUBLIC | v.PRIVATE),
        "!show": Command(_callback_show, v.PUBLIC | v.PRIVATE),
        "!version": Command(_callback_version, v.PUBLIC | v.PRIVATE),
        #TODO !steal
    }

    admin_commands = {
        "!!help": Command(_callback_admin_help, v.PUBLIC | v.PRIVATE),
        "!!fight": Command(_callback_admin_fight, v.PUBLIC),
        "!!heal": Command(_callback_admin_heal, v.PUBLIC | v.PRIVATE),
        "!!level": Command(_callback_admin_level, v.PUBLIC | v.PRIVATE),
        "!!exp": Command(_callback_admin_exp, v.PUBLIC | v.PRIVATE),
        "!!say": Command(_callback_admin_say, v.PRIVATE),
        "!!out": Command(_callback_admin_out, v.PUBLIC | v.PRIVATE),
    }
