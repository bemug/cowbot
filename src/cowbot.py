import irc.bot #type: ignore
from time import sleep
from typing import Any, Callable, Coroutine
from aftermath import *
from game import *
from indian import *
from utils import *
from datetime import datetime

def trace(msg):
        now = datetime.now()
        print("[" + str(now) + "] " + msg)


class Command():
    #TODO replace first any with Cowbot
    def __init__(self, callback: Callable[[Any, Any, Any, Any], Coroutine[Any, Any, None]], help_message: str) -> None:
        self.callback = callback
        self.help_message = help_message


class Cowbot(irc.bot.SingleServerIRCBot): #type: ignore
    msg_wait = 1

    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.game = Game()

    def is_admin(self, nick):
        #TODO config file
        return nick == "zoologist"

    def msg(self, target, msg):
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
        trace("Ping received")
        #Target is the irc serveur, change it to our channel
        e.target = self.channel

        now = datetime.now()
        hour_str = now.strftime("%Hh%M")
        #Check opening hours
        if not self.game.opened and Game.is_open_hour():
            self.game.open()
            trace("Open")
            self.msg(e.target, f"Il est {hour_str}, le saloon ouvre ses portes ☀️")
        #Check if a fight is available before closing, to not miss any fights
        if self.game.opened: #Skip missed fights on closed hours
            for fight_time in self.game.fight_times:
                if now > fight_time: #TODO use same reference of time, put 'now' in game
                    trace("Fight")
                    self._fight(e.target)
                    self.game.fight_times.pop(0)
                    break
        if self.game.opened and not Game.is_open_hour():
            self.game.close()
            trace("Close")
            #TODO today's earnings
            self.msg(e.target, f"Il est {hour_str}, le saloon ferme 🌑")

    def on_join(self, c, e):
        #As we join the channel, do the same thing as if we're pinged
        self.on_ping(c, e)

    def on_privmsg(self, c, e):
        #Treat privmsg as nomal messages for now, but answer in public
        e.target = self.channel
        self.on_pubmsg(c, e)

    def on_pubmsg(self, c, e):
        print(e) #TODO debug
        message: str = e.arguments[0]
        if message.startswith("!!") and self.is_admin(e.source.nick):
            command_array = self.admin_commands
        elif message.startswith('!'):
            command_array = self.commands
        else:
            return

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

    def debug_start(self):
        self.game.add_player("zoologist")


    ### Player commands ###

    def _callback_help(self, target: int, source, args: str) -> None:
        for command in self.commands:
            self.msg(target, command + " : " + self.commands[command].help_message)

    def _callback_pitch(self, target, source, args: str) -> None:
        self.msg(target, "Bienvenue dans mon saloon, étranger. Installez vous. J'ai là un excellent whisky, vous devriez le goûter.")
        self.msg(target, "Dites, j'ai entendu dire que vous n'aimiez pas trop les indiens ? Ils me mènent la vie dure ces temps-ci. Ils débarquent dans mon saloon et piquent dans la caisse. Peut être que vous pourriez en dessouder quelques-uns pour moi ? Je saurais me montrer redevable.")

    def _callback_join(self, target, source, args: str) -> None:
        player: Player = self.game.add_player(source)
        if not player:
            player = self.game.find_player(source)
            self.msg(target, f"{ERR} Tu es déjà à l'intérieur du saloon.")
            return
        self.msg(target, f"Bienvenue dans le saloon.")

    def _callback_status(self, target, source, args: str) -> None:
        player: Player = self.game.find_player(source)
        if not player:
            self.msg(target, f"{ERR} On ne se connait pas encore ? Entre d'abord dans le saloon.")
            return
        msg: str = "{} niveau {} : [{}{}/{}{}{}] [{}{}/{}{}{}]".format(
                player.no_hl_str(),
                player.level,
                colors["blue"], player.exp, player.get_max_exp(), icons["exp"], colors["reset"],
                colors["red"], player.hp, player.get_max_hp(), icons["hp"], colors["reset"],
            )
        self.msg(target, msg)

    def _callback_cash(self, target, source, args: str) -> None:
        log: str = "Le contenu du tiroir-caisse est actuellement de {}{}{}{}.".format(
            colors["yellow"], self.game.get_cash(), icons["cash"], colors["reset"],
        )
        self.msg(target, log)


    ### Admin commands ###

    def _callback_admin_help(self, target: int, source, args: str) -> None:
        for command in self.admin_commands:
            self.msg(target, command + " : " + self.admin_commands[command].help_message)

    def _callback_admin_fight(self, target, source, args: str) -> None:
        self._fight(target)

    def _fight(self, target) -> None:
        log: str = ""
        number_str = ""

        self.game.start_fight()

        if len(self.game.indians) > 1:
            number_str = "nt"
        self.msg(target, f"{list_str(self.game.indians)} débarque{number_str} dans le saloon.")
        sleep(Cowbot.msg_wait)
        while not self.game.is_fight_over():
            am: Aftermath = self.game.process_fight()
            #armor sign will be ⛊
            log = "{} tire {}{}{}{} sur {} [{}{}/{}{}{}].".format(
                    am.source.no_hl_str(),
                    colors["orange"], am.damage, icons["dmg"],colors["reset"],
                    am.target.no_hl_str(),
                    colors["red"], am.target.hp, am.target.get_max_hp(), icons["hp"], colors["reset"],
                )
            self.msg(target, log)
            if am.target.is_dead():
                self.msg(target, f"{am.target} est à terre.")
            sleep(Cowbot.msg_wait)

        #Backup levels for display
        levels = [player.level for player in self.game.players]
        cash_change = self.game.end_fight()

        if cash_change > 0:
            log = "VICTOIRE. {} possède{} {}{}{}{}, que je place dans le tiroir-caisse [{}{}{}{}].".format(
                    list_str(self.game.indians),
                    number_str,
                    colors["yellow"], cash_change, icons["cash"], colors["reset"],
                    colors["yellow"], self.game.get_cash(), icons["cash"], colors["reset"],
                )
            self.msg(target, log)

            i=0
            for player in self.game.players:
                if player.level != levels[i]:
                    log = "{} passe au niveau {} [{}{}/{}{}{}].".format(
                            player,
                            player.level,
                            colors["blue"], player.exp, player.get_max_exp(), icons["exp"], colors["reset"],
                        )
                    self.msg(target, log)
                i += 1
            #TODO loot
        else:
            log = "DEFAITE. {} vole{} {}{}{}{} dans le tiroir-caisse [{}{}{}{}], et s'échappe{}.".format(
                    list_str(self.game.indians),
                    number_str,
                    colors["yellow"], -cash_change, icons["cash"], colors["reset"],
                    colors["yellow"], self.game.get_cash(), icons["cash"], colors["reset"],
                    number_str,
                )
            self.msg(target, log)
        self.game.clean_after_fight()

    def _callback_admin_cash(self, target, source, args: str) -> None:
        if len(args) != 1:
            self.msg(target, "!cash <cash>")
            return
        try:
            self.game.cash = int(args[0])
        except ValueError:
            self.msg(target, f"'{args[0]}' n'est pas un nombre.")
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
            player.level = int(args[0])
        except ValueError:
            self.msg(target, f"{ERR} Le niveau doit être un nombre.")
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
            exp: int = int(args[0])
        except ValueError:
            self.msg(target, f"{ERR} L'experience doit être un nombre.")
            return
        if exp > player.get_max_exp():
            self.msg(target, f"{ERR} L'experience de {player.no_hl_str()} ne peut dépasser {player.get_max_exp()}.")
            return
        player.exp = exp
        self.msg(target, f"Experience du joueur {player.level}.")


    ### Commands lists ###

    commands = {
        "!help": Command(_callback_help, "Affiche l'aide"),
        "!pitch": Command(_callback_pitch, "Conte l'histoire"),
        "!join": Command(_callback_join, "Entre dans le saloon"),
        "!status": Command(_callback_status, "Affiche ton statut"),
        "!cash": Command(_callback_cash, "Affiche le contenu du tiroir-caisse"),
    }

    admin_commands = {
        "!!help": Command(_callback_admin_help, "Affiche l'aide administrateur"),
        "!!fight": Command(_callback_admin_fight, "Déclenche instantanément un combat"),
        "!!cash": Command(_callback_admin_cash, "Change le cash dans le tiroir-caisse"),
        "!!heal": Command(_callback_admin_heal, "Soigne un joueur"),
        "!!level": Command(_callback_admin_level, "Change le niveau d'un joueur"),
        "!!exp": Command(_callback_admin_exp, "Change l'experience d'un joueur"),
    }


def main():
    import sys

    if len(sys.argv) != 4:
        print("Usage: cowbot <server[:port]> <channel> <nickname>")
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

    bot = Cowbot(channel, nickname, server, port) #type: ignore

    bot.debug_start()

    bot.start()


if __name__ == "__main__":
    main()
