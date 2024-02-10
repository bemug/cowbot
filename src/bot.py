import irc.bot #type: ignore
from time import sleep
from typing import Any, Callable, Coroutine
from aftermath import *
from game import *
from indian import *
from utils import *
from datetime import datetime


class Command():
    #TODO replace first any with Bot
    def __init__(self, callback: Callable[[Any, Any, Any, Any], Coroutine[Any, Any, None]], help_message: str) -> None:
        self.callback = callback
        self.help_message = help_message


class Bot(irc.bot.SingleServerIRCBot): #type: ignore
    msg_wait = 1
    after_fight_wait = timedelta(milliseconds=10)


    ### IRC callbacks ###

    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.game = Game()
        self.last_fight_time = datetime.now()

    def is_admin(self, nick):
        #TODO config file
        return nick == "zoologist"

    def msg(self, target, msg):
        trace("Sent to " + target + ": \"" + msg + "\"")
        self.connection.privmsg(target, msg)

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
        #Target is the irc server, change it to our channel
        e.target = self.channel
        self._process_time(c, e)

    def on_join(self, c, e):
        #As we join the channel, do the same thing as if we're pinged
        self.on_ping(c, e)

    def on_privmsg(self, c, e):
        #Treat privmsg as nomal messages for now, but answer in public
        e.target = self.channel
        self.on_pubmsg(c, e)

    def on_pubmsg(self, c, e):
        self._process_command(c, e)


    ### Game FSM and display ###

    def debug_start(self):
        self.game.loot.append(Weapon("Colt", 1, 50))
        self.game.loot.append(Weapon("Revolver", 2, 0))
        self.game.loot.append(Armor("Stetson en laine", 2, 50))
        self.game.loot.append(Armor("Stetson en feutre", 3, 0))

    def _process_time(self, c, e):
        fmt= "%Hh%M"
        #Check opening hours
        if not self.game.opened and Game.is_open_hour():
            trace("Opening game")
            self.game.open()
            self.msg(e.target, f"Il est {Game.hour_open.strftime(fmt)}, le saloon ouvre ses portes 🌅")
        #Check if a fight is available before closing, to not miss any fights
        if self.game.opened: #Skip missed fights on closed hours, and don't heal
            if self.game.is_heal_time():
                self.game.heal_players()
            if self.game.is_fight_time():
                self._fight(e.target)
        if self.game.opened and not Game.is_open_hour():
            self.game.close()
            trace("Closing game")
            #TODO today's earnings
            self.msg(e.target, f"Il est {Game.hour_close.strftime(fmt)}, le saloon ferme 🌠")

    def _process_command(self, c, e):
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
            command_array[command]
        except KeyError:
            self.msg(e.target, f"{ERR} Commande inconnue : {message}")
            return
        command_array[command].callback(self, e.target, e.source.nick, args)

    def _fight(self, target) -> None:
        log: str = ""
        number_str: str = ""
        step: int = 1

        try:
            self.game.start_fight()
        except RuntimeError:
            #TODO steal money instead
            self.msg(target, f"Il n'y a personne pour defendre le saloon !")
            return

        if len(self.game.indians) > 1:
            number_str = "nt"
        self.msg(target, f"{list_str(self.game.indians)} débarque{number_str} dans le saloon {list_str(self.game.players)} !")
        sleep(Bot.msg_wait)
        while not self.game.is_fight_over():
            #Fight
            am: Aftermath = self.game.process_fight()

            #Construct log
            log = f"{step}. {am.source.no_hl_str()} tire sur {am.target.no_hl_str()} : "

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
                with_crit = decor_str(str(am.source.weapon.crit), decorations["crit"])
            if did_miss:
                with_miss = decor_str(str(am.source.armor.miss), decorations["miss"])
            log += " et ".join(filter(None, [with_crit, with_miss]))

            log += ". Reste {}.".format(decor_str(f"{am.target.hp}/{am.target.get_max_hp()}", decorations["hp"]))

            self.msg(target, log)

            if am.target.is_dead():
                self.msg(target, f"{am.target} est à terre.")

            step += 1
            sleep(Bot.msg_wait)

        #Backup levels for display
        levels = [player.level for player in self.game.players]
        cash_change = self.game.end_fight()

        if cash_change > 0:
            log = "VICTOIRE. {} possède{} {}, que je place dans le tiroir-caisse ({}).".format(
                    list_str(self.game.indians),
                    number_str,
                    decor_str(str(cash_change), decorations["cash"]),
                    decor_str(str(self.game.get_cash()), decorations["cash"]),
                )
            self.msg(target, log)

            for i, player in enumerate(self.game.players):
                if player.level != levels[i]:
                    log = "{} passe au niveau {} ({}).".format(
                            player,
                            player.level,
                            decor_str(f"{player.exp}/{player.get_max_exp()}", decorations["exp"]),
                        )
                    self.msg(target, log)

            self._show_loot(target)
        else:
            log = "DEFAITE. {} vole{} {} dans le tiroir-caisse ({}), et s'échappe{}.".format(
                    list_str(self.game.indians),
                    number_str,
                    decor_str(str(-cash_change), decorations["cash"]),
                    decor_str(str(self.game.get_cash()), decorations["cash"]),
                    number_str,
                )
            self.msg(target, log)
        self.game.clean_after_fight()
        #Start a time to ignore all new messages that came inbetween the fight sleeps
        self.last_fight_time = datetime.now()

    def _str_item(self, item):
        if item == None:
            return None
        if isinstance(item, Weapon):
            decor = [decorations["dmg"], decorations["crit"]]
        elif isinstance(item, Armor):
            decor = [decorations["arm"], decorations["miss"]]
        else:
            trace("Unknown item type, ignoring.")
        ret = str(item) + " : " + decor_str(str(item.attr1), decor[0])
        if item.attr2 > 0:
            ret += " ; " + decor_str(str(item.attr2), decor[1])
        return ret

    def _show_loot(self, target):
        log = "Dépouille →"
        items_log = ""
        for i, item in enumerate(self.game.loot):
            if item != None:
                items_log += f"  [{i}] {self._str_item(item)}"
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
        for command in self.commands:
            self.msg(target, command + " : " + self.commands[command].help_message)

    def _callback_pitch(self, target, source, args: str) -> None:
        self.msg(target, "Bienvenue dans mon saloon, étranger. Installez vous. J'ai là un excellent whisky, vous devriez le goûter.")
        self.msg(target, "Dites, j'ai entendu dire que vous n'aimiez pas trop les indiens ? Ils me mènent la vie dure ces temps-ci. Ils débarquent dans mon saloon et piquent dans la caisse. Peut être que vous pourriez en dessouder quelques-uns pour moi ? Je saurais me montrer redevable.")

    def _callback_join(self, target, source, args: str) -> None:
        self.msg(target, f"Bienvenue dans le saloon.")

    def _callback_status(self, target, source, args: str) -> None:
        player: Player = self.game.find_player(source, True)
        msg: str = "Cowboy niv. {} → {} ; {} ; {}.".format(
                player.level,
                decor_str(f"{player.get_damage()}", decorations["dmg"]),
                decor_str(f"{player.hp}/{player.get_max_hp()}", decorations["hp"]),
                decor_str(f"{player.exp}/{player.get_max_exp()}", decorations["exp"]),
            )
        if player.weapon != None or player.armor != None:
            msg += "  Equipement → " + " et ".join(filter(None, ([self._str_item(player.weapon), self._str_item(player.armor)]))) + "."

        self.msg(target, msg)

    def _callback_cash(self, target, source, args: str) -> None:
        log: str = "Le contenu du tiroir-caisse est actuellement de {}.".format(
            decor_str(str(self.game.get_cash()), decorations["cash"])
        )
        self.msg(target, log)

    def _callback_inventory(self, target, source, args: str) -> None:
        player: Player = self.game.find_player(source, True)
        log = "Inventaire →"
        items_log = ""
        for i, item in enumerate(player.inventory):
            if item != None:
                str_equipped = ""
                if player.has_equipped(item):
                    str_equipped = "[E]"
                items_log += f"  [{i}]{str_equipped} {self._str_item(item)}"
        if items_log == "":
            log += " Vide"
        self.msg(target, log + items_log)

    def _callback_loot(self, target, source, args: str) -> None:
        if len(args) == 0:
            self._show_loot(target)
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            item = self.game.do_loot(player, index)
        except IndexError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet numéro {int(args[0])} dans la dépouille.")
            return
        self.msg(target, f"{self._str_item(item)} ramassé.")

    def _callback_drop(self, target, source, args: str) -> None:
        if len(args) != 1:
            self.msg(target, "!drop <index>")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            item, unequipped = self.game.do_drop(player, index)
        except IndexError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet numéro {int(args[0])} dans ton inventaire.")
            return
        str_unequipped = ""
        if unequipped:
            str_unequipped = "d'abord déséquipé, et "
        self.msg(target, f"{self._str_item(item)} {str_unequipped}déposé.")

    def _callback_equip(self, target, source, args: str) -> None:
        if len(args) != 1:
            self.msg(target, "!equip <index>")
            return
        try:
            index = self._parse_uint(target, args[0])
        except ValueError:
            return
        player: Player = self.game.find_player(source, True)
        try:
            item = self.game.do_equip(player, index)
        except IndexError:
            self.msg(target, f"{ERR} Il n'y a pas d'objet numéro {int(args[0])} dans ton inventaire.")
            return
        except ValueError:
            self.msg(target, f"{ERR} Tu ne peux pas équipper ça.")
            return
        self.msg(target, f"{self._str_item(item)} équipé.")

    def _callback_version(self, target, source, args: str) -> None:
        self.msg(target, git_version())


    ### Admin commands ###

    def _callback_admin_help(self, target: int, source, args: str) -> None:
        for command in self.admin_commands:
            self.msg(target, command + " : " + self.admin_commands[command].help_message)

    def _callback_admin_fight(self, target, source, args: str) -> None:
        self._fight(target)

    def _callback_admin_cash(self, target, source, args: str) -> None:
        if len(args) != 1:
            self.msg(target, "!cash <cash>")
            return
        try:
            self.game.cash = self._parse_uint(target, args[0])
        except ValueError:
            return
        self.msg(target, f"Il y a à présent {self.game.cash}$ dans le tiroir-caisse.")

    def _callback_admin_heal(self, target, source, args: str) -> None:
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

    def _callback_admin_icons(self, target, source, args: str) -> None:
        self.msg(target, "Icones : "  + ''.join(icon for icon in icons.values()))

    ### Commands lists ###

    commands = {
        "!help": Command(_callback_help, "Affiche l'aide"),
        "!pitch": Command(_callback_pitch, "Conte l'histoire"),
        "!join": Command(_callback_join, "Entre dans le saloon"),
        "!cash": Command(_callback_cash, "Affiche le contenu du tiroir-caisse"),
        "!status": Command(_callback_status, "Affiche ton statut"),
        "!inventory": Command(_callback_inventory, "Affiche ton inventaire"),
        "!loot": Command(_callback_loot, "Prend un objet d'une dépouille pour la placer dans ton inventaire"),
        "!drop": Command(_callback_drop, "Place un objet de ton inventaire dans la dépouille"),
        "!equip": Command(_callback_equip, "Equipe un objet de ton inventaire"),
        "!version": Command(_callback_version, "Affiche la version du jeu"),
    }

    admin_commands = {
        "!!help": Command(_callback_admin_help, "Affiche l'aide administrateur"),
        "!!fight": Command(_callback_admin_fight, "Déclenche instantanément un combat"),
        "!!cash": Command(_callback_admin_cash, "Change le cash dans le tiroir-caisse"),
        "!!heal": Command(_callback_admin_heal, "Soigne un joueur"),
        "!!level": Command(_callback_admin_level, "Change le niveau d'un joueur"),
        "!!exp": Command(_callback_admin_exp, "Change l'experience d'un joueur"),
        "!!icons": Command(_callback_admin_icons, "Affiche les icones"),
    }


def main():
    import sys

    if len(sys.argv) != 4:
        print("Usage: bot <server[:port]> <channel> <nickname>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]

    bot = Bot(channel, nickname, server, port) #type: ignore

    bot.debug_start()

    bot.start()


if __name__ == "__main__":
    main()
