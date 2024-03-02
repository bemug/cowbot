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
            if args[0] == "help" or len(args) not in expected_len:
                return True
        except IndexError:
            pass
        return False


class Bot(irc.bot.SingleServerIRCBot): #type: ignore
    msg_wait = 2
    after_fight_wait = timedelta(milliseconds=10)


    ### IRC callbacks ###

    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.game = Game.load()
        if self.game.speed > 1:
            Bot.msg_wait = 1
        self.last_fight_time = datetime.now()

    def is_admin(self, nick):
        #TODO config file
        return nick == "zoologist"

    def msg(self, target, msg):
        #This lib is fucked up.
        #It could either let me know how much byte it sends in a message, or either wrap lines for me.
        max_chars = 512 #IRC protocol limit excluding CR/LF
        max_chars -= 25 #So we should be safe
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
        #As we join the channel, do the same thing as if we're pinged
        self.on_ping(c, e)

    def on_privmsg(self, c, e):
        #Talk to our source
        target = e.source.split('!',1)[0]
        self._process_command(c, e, target)

    def on_pubmsg(self, c, e):
        self._process_command(c, e, e.target)

    def on_part(self, c, e):
        self.remove_player_from_game(e.source.nick)
    def on_kick(self, c, e):
        self.remove_player_from_game(e.source.nick)
    def on_quit(self, c, e):
        self.remove_player_from_game(e.source.nick)


    ### Game FSM and display ###

    def remove_player_from_game(self, source):
        player: Player = self.game.find_player(source)
        if not player:
            return
        if player in self.game.players_ingame:
            trace(f"Player {player} quit, remove him from ingame")
            self.game.players_ingame.remove(player)
        else:
            trace(f"Player {player} quit, but was not ingame. Do nothing")

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
            args: str = message.split(' ')[1:]
        except IndexError:
            pass
        try:
            #Check it exists
            cmd = command_array[command]
        except KeyError:
            self.msg(target, f"{ERR} Commande inconnue : {message}")
            return

        #Check you have the right to sue this command here
        if target == self.channel and not cmd.visibility & v.PUBLIC:
            self.msg(target, f"{ERR} Tu ne peux pas utiliser la commande '{message}' en public.")
            return
        elif target != self.channel and not cmd.visibility & v.PRIVATE:
            self.msg(target, f"{ERR} Tu ne peux pas utiliser la commande '{message}' en privé.")
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
        sleep(Bot.msg_wait)
        while not self.game.is_fight_over():
            #Fight
            am: Aftermath = self.game.process_fight()

            #Construct log
            log = f"{step}. {am.source.no_hl_str()}"
            if am.target != am.rival:
                log += " manque sa cible, et"
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
                with_crit = decor_str(str(am.source.weapon.attr2), decorations["crit"])
            if did_miss:
                with_miss = decor_str(str(am.source.armor.attr2), decorations["miss"])
            log += " et ".join(filter(None, [with_crit, with_miss]))

            log += ". Reste {}.".format(decor_str(f"{am.target.hp}/{am.target.get_max_hp()}", decorations["hp"]))

            self.msg(target, log)

            if am.target.is_dead():
                sleep(0.5)
                self.msg(target, f"{am.target} est à terre.")

            step += 1
            sleep(Bot.msg_wait)

        #Backup levels for display
        levels = [player.level for player in self.game.players]
        cash_change = self.game.end_fight()

        if cash_change > 0:
            log = "VICTOIRE. Pendant la bagarre j'ai vendu pour {} de consommations. J'ai placé cet argent dans le tiroir-caisse ({}).".format(
                    decor_str(str(cash_change), decorations["cash"]),
                    decor_str(str(self.game.get_cash()), decorations["cash"]),
                )
            self.msg(target, log)
            sleep(Bot.msg_wait)

            for i, player in enumerate(self.game.players):
                if player.level != levels[i]:
                    log = "{} passe au {} ({}).".format(
                            player,
                            decor_str(f"niveau {player.level}", decorations["level"]),
                            decor_str(f"{player.exp}/{player.get_max_exp()}", decorations["exp"]),
                        )
                    self.msg(target, log)
                    sleep(Bot.msg_wait)

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

    def _str_item(self, item, slot = -1, equipped = False):
        if item == None:
            return None
        ret = ""
        if slot != -1:
            ret += f"[{slot}]"
        if isinstance(item, Weapon):
            decor = [decorations["dmg"], decorations["crit"]]
        elif isinstance(item, Armor):
            decor = [decorations["arm"], decorations["miss"]]
        elif isinstance(item, Consumable):
            decor = [decorations["hp"]]
            return ret + " " + str(item) + " " + decor_str(str(item.heal), decor[0])
        else:
            trace("Unknown item type, ignoring.")
            return
        if equipped:
            ret += "[E]"
        if ret != "":
           ret += " " 
        ret += str(item) + " " + decor_str(str(item.attr1), decor[0])
        if item.attr2 > 0:
            ret += " " + decor_str(str(item.attr2), decor[1])
        return ret

    def _show_loot(self, target):
        log = "Dépouille :"
        items_log = ""
        for i, item in sorted(self.game.loot.items()):
            items_log += f"  {self._str_item(item, i)}"
        if items_log == "":
            log += " Vide"
        self.msg(target, log + items_log)

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


    ### Player commands ###

    def _callback_help(self, target: int, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!help : Affiche l'aide")
            return
        msg = "Commandes : "
        msg += decor_str(' '.join(self.commands), decorations['cmd'])
        msg += ". Taper '!<command> help' pour plus. Certaines commandes sont également accessibles par message privé."
        self.msg(target, msg)

    def _callback_pitch(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!pitch : Raconte l'histoire du lieu")
            return
        self.msg(target, "Bienvenue dans mon saloon, étranger. Installez vous. J'ai là un excellent whisky, goûtez-le.")
        sleep(0.5)
        self.msg(target, "Dites, j'ai entendu dire que vous n'aimiez pas trop les indiens ? Ils me mènent la vie dure ces temps-ci. Ils débarquent dans mon saloon et piquent dans la caisse. Peut être que vous pourriez en dessouder quelques-uns pour moi ? Je saurais me montrer redevable.")
        sleep(0.5)
        self.msg(target, f"Vous devriez entrer, et attendre ici. Je les connais bien ils ne devraient pas tarder.")

    def _callback_enter(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!enter : Entre dans le saloon.")
            return
        player: Player = self.game.find_player(source, True)
        if not player in self.game.players_ingame:
            self.game.players_ingame.append(player)
            #TODO voice
            self.msg(target, f"Bienvenue dans le saloon.")
        else:
            self.msg(target, f"{ERR} Tu es déjà dans le saloon.")

    def _callback_leave(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!leave : Quitte le saloon.")
            return
        player: Player = self.game.find_player(source, True)
        if player in self.game.players_ingame:
            self.game.players_ingame.remove(player)
            #TODO devoice
            self.msg(target, f"A la prochaine cowboy.")
        else:
            self.msg(target, f"{ERR} Tu es déjà hors du saloon.")

    def _callback_status(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!status : Affiche ton statut.")
            return
        player: Player = self.game.find_player(source, True)
        msg: str = "Cowboy "
        msg += decor_str(f"niveau {player.level}", decorations["level"])
        if player.weapon != None or player.armor != None:
            msg += " équipé de " + " et ".join(filter(None, ([self._str_item(player.weapon), self._str_item(player.armor)])))
        if player in self.game.players_ingame:
            msg += f", actuellement {decor_str('dans', decorations['position'])} le saloon."
        else:
            msg += f", actuellement {decor_str('hors', decorations['position'])} du saloon."
        msg += " {} {} {}.".format(
                decor_str(f"{player.get_damage()}", decorations["dmg"]),
                decor_str(f"{player.hp}/{player.get_max_hp()}", decorations["hp"]),
                decor_str(f"{player.exp}/{player.get_max_exp()}", decorations["exp"]),
            )

        self.msg(target, msg)

    def _callback_cash(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!cash : Affiche le contenu du tiroir-caisse.")
            return
        log: str = "Le contenu du tiroir-caisse est de {}.".format(
            decor_str(str(self.game.get_cash()), decorations["cash"])
        )
        self.msg(target, log)

    def _callback_inventory(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!inventory : Affiche ton inventaire.")
            return
        player: Player = self.game.find_player(source, True)
        log = "Inventaire :"
        items_log = ""
        for i, item in sorted(player.inventory.items()):
            items_log += f"  {self._str_item(item, i, player.has_equipped(item))}"
        if items_log == "":
            log += " Vide"
        self.msg(target, log + items_log)

    def _callback_loot(self, target, source, args: str) -> None:
        if Command.help_asked(args, [0]):
            self.msg(target, "!loot : Affiche la dépouille")
            return
        self._show_loot(target)

    def _callback_pick(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!pick <index> : Recupère l'objet 'index' de la dépouille pour le placer dans ton inventaire")
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
        self.msg(target, f"{self._str_item(item, index)} ramassé dans le slot [{slot}].")

    def _callback_drop(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!drop <index> : Place l'objet 'index' de ton inventaire dans la dépouille")
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
            str_unequipped = "d'abord déséquipé, puis "
        self.msg(target, f"{self._str_item(item, index, unequipped)} {str_unequipped}déposé dans le slot [{slot}].")

    def _callback_equip(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!equip <index> : Equipe l'objet 'index' de ton inventaire")
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
        msg =  f"{self._str_item(item, index)} équipé"
        if old_item != None:
            old_slot = player.get_slot(old_item)
            msg += f" à la place de {self._str_item(old_item, old_slot)}"
        msg += "."
        self.msg(target, msg)

    def _callback_drink(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!drink <index> : Bois l'objet 'index' de ton inventaire")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            item = self.game.do_drink(player, index)
        except KeyError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet numéro [{int(args[0])}] dans ton inventaire.")
            return
        except ValueError:
            self.msg(target, f"{ERR} Cet object ne peut pas être bu.")
            return
        msg = f"{self._str_item(item, index)} bu ("
        msg += decor_str(f"{player.hp}/{player.get_max_hp()}", decorations["hp"])
        msg += ")."
        self.msg(target, msg)

    def _callback_version(self, target, source, args: str) -> None:
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
            self.msg(target, f"{ERR} Le joueur {source} n'existe pas.")
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
            self.msg(target, f"{ERR} Le joueur {source} n'existe pas.")
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
            self.msg(target, f"{ERR} Le joueur {source} n'existe pas.")
            return
        try:
            exp: int = self._parse_uint(target, args[0])
        except ValueError:
            return
        if exp > player.get_max_exp():
            self.msg(target, f"{ERR} L'experience de {player.no_hl_str()} ne peut dépasser {player.get_max_exp()}.")
            return
        player.exp = exp
        self.msg(target, f"Experience du joueur {player.exp}.")

    def _callback_admin_say(self, target, source, args: str) -> None:
        if Command.help_asked(args, [1]):
            self.msg(target, "!!say <message> : Parle")
            return
        self.msg(self.channel, ' '.join(args))

    ### Commands lists ###

    commands = {
        "!help": Command(_callback_help, v.PUBLIC | v.PRIVATE),
        "!pitch": Command(_callback_pitch, v.PUBLIC | v.PRIVATE),
        "!enter": Command(_callback_enter, v.PUBLIC),
        "!leave": Command(_callback_leave, v.PUBLIC),
        "!cash": Command(_callback_cash, v.PUBLIC | v.PRIVATE),
        "!status": Command(_callback_status, v.PUBLIC | v.PRIVATE),
        "!inventory": Command(_callback_inventory, v.PUBLIC | v.PRIVATE),
        "!loot": Command(_callback_loot, v.PUBLIC | v.PRIVATE),
        "!pick": Command(_callback_pick, v.PUBLIC),
        "!drop": Command(_callback_drop, v.PUBLIC),
        "!equip": Command(_callback_equip, v.PUBLIC),
        "!drink": Command(_callback_drink, v.PUBLIC | v.PRIVATE),
        "!version": Command(_callback_version, v.PUBLIC | v.PRIVATE),
        #TODO !pack
        #TODO !swap
        #TODO !steal
        #TODO !show
    }

    admin_commands = {
        "!!help": Command(_callback_admin_help, v.PUBLIC | v.PRIVATE),
        "!!fight": Command(_callback_admin_fight, v.PUBLIC),
        "!!heal": Command(_callback_admin_heal, v.PUBLIC | v.PRIVATE),
        "!!level": Command(_callback_admin_level, v.PUBLIC | v.PRIVATE),
        "!!exp": Command(_callback_admin_exp, v.PUBLIC | v.PRIVATE),
        "!!say": Command(_callback_admin_say, v.PRIVATE),
    }
