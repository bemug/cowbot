import irc.bot #type: ignore
from time import sleep
from typing import Any, Callable, Coroutine
from aftermath import *
from game import *
from indian import *
from utils import *


class Command():
    #TODO replace first any with Cowbot
    def __init__(self, callback: Callable[[Any, Any, Any, Any], Coroutine[Any, Any, None]], help_message: str) -> None:
        self.callback = callback
        self.help_message = help_message


class Cowbot(irc.bot.SingleServerIRCBot): #type: ignore
    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.game = Game()

    def _callback_help(self, target: int, source, args: str) -> None:
        for command in self.commands:
            self.connection.privmsg(target, command + " : " + self.commands[command].help_message)

    def _callback_pitch(self, target, source, args: str) -> None:
        self.connection.privmsg(target, "Bienvenue dans mon saloon, étranger. Installez vous. J'ai là un excellent whisky, vous devriez le goûter.")
        self.connection.privmsg(target, "Dites, j'ai entendu dire que vous n'aimiez pas trop les indiens ? Ils me mènent la vie dure ces temps-ci. Ils débarquent dans mon saloon et piquent dans la caisse. Peut être que vous pourriez en dessouder quelques-uns pour moi ? Je saurais me montrer redevable.")

    def _callback_join(self, target, source, args: str) -> None:
        self.game.add_player(source)
        self.connection.privmsg(target, f"join {source}.")

    def _callback_find(self, target, source, args: str) -> None:
        self.game.find_indian()
        self.connection.privmsg(target, f"find {self.game.indian}.")

    def _callback_fight(self, target, source, args: str) -> None:
        log: str = ""

        self.game.start_fight()
        self.connection.privmsg(target, f"{self.game.indian} débarque dans le saloon.")
        sleep(1)
        while not self.game.is_fight_over():
            am: Aftermath = self.game.process_fight()
            log = "{} frappe {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
                    str(am.source),
                    str(am.target),
                    colors["red"],
                    am.from_hp - am.to_hp,
                    colors["reset"], colors["green"],
                    am.from_hp,
                    colors["reset"], colors["green"],
                    am.to_hp,
                    colors["reset"],
                )
            self.connection.privmsg(target, log)
            if am.target.is_dead():
                self.connection.privmsg(target, f"{am.target} décède. ✝")
            sleep(1)
        #TODO msg + loot
        self.connection.privmsg(target, "Combat terminé.")

    def _callback_cash(self, target, source, args: str) -> None:
        if len(args) != 1:
            self.connection.privmsg(target, "!cash <cash>")
            return
        try:
            self.game.cash = int(args[0])
        except ValueError:
            self.connection.privmsg(target, f"'{args[0]}' n'est pas un nombre.")
            return
        self.connection.privmsg(target, f"Il y a à présent {self.game.cash}$ dans le tiroir-caisse.")

    commands = {
        "!help": Command(_callback_help, "Affiche cette aide"),
        "!pitch": Command(_callback_pitch, "Conte l'histoire"),
        "!join": Command(_callback_join, "Rejoins mon armée"),
        "!find": Command(_callback_find, "Cherche un monstre à combattre"),
        #"!status": Command(_callback_status, "Affiche ton statut"),
        "!fight": Command(_callback_fight, "Lance un combat"),
        "!cash": Command(_callback_cash, "Change le cash dans le tiroir-caisse"),
    }

    def get_users(self):
        users: List = list(self.channels.get(self.channel).users())
        users.remove(self.connection.nickname)
        return sorted(users)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        print(e) #TODO debug
        message: str = e.arguments[0]
        if message.startswith('!'):
            command: str = message.split(' ', 1)[0]
            args: str = None
            try:
                args: str = message.split(' ')[1:]
            except IndexError:
                pass
            try:
                self.commands[message.split(' ')[0]].callback(self, e.target, e.source.nick, args)
            except KeyError:
                self.connection.privmsg(e.target, f"Commande inconnue : {message}")
        return

    def debug_start(self):
        self.game.add_player("zoologist")
        self.game.find_indian()

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
