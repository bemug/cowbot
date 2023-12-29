import irc.bot #type: ignore
from time import sleep
from typing import Any, Awaitable, Callable, Coroutine
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

    def _callback_help(self, target: int, source, *argv: Any) -> None:
        for name in self.commands:
            self.connection.privmsg(target, name + " : " + self.commands[name].help_message)

    def _callback_pitch(self, target, *argv: Any) -> None:
        self.connection.privmsg(target, "pitch")

    def _callback_join(self, target, source, *argv: Any) -> None:
        self.dungeon.add_player(source)
        self.connection.privmsg(target, f"join {source}.")

    def _callback_find(self, target, source, *argv: Any) -> None:
        self.dungeon.generate_indian()
        self.connection.privmsg(target, f"find {self.dungeon.indian.name} {self.dungeon.indian.adjective}.")

    def _callback_fight(self, target, source, *argv: Any) -> None:
        while self.dungeon.indian.is_alive():
            self.dungeon.fight()
            if self.dungeon.turn == Turn.PLAYER:
                log = "{} frappe {} {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
                        self.dungeon.player.name,
                        self.dungeon.indian.name,
                        self.dungeon.indian.adjective,
                        colors["red"],
                        self.dungeon.player.damage,
                        colors["reset"], colors["green"],
                        "???",
                        colors["reset"], colors["green"],
                        self.dungeon.indian.hp,
                        colors["reset"],
                    )
            else:
                log = "{} {} frappe {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
                        self.dungeon.indian.name,
                        self.dungeon.indian.adjective,
                        self.dungeon.player.name,
                        colors["red"],
                        self.dungeon.indian.damage,
                        colors["reset"], colors["green"],
                        "???",
                        colors["reset"], colors["green"],
                        self.dungeon.player.hp,
                        colors["reset"],
                    )
            self.connection.privmsg(target, log)
            sleep(1)
        self.dungeon.clear_indian()

    commands = {
        "!help": Command(_callback_help, "Affiche cette aide"),
        "!pitch": Command(_callback_pitch, "Conte l'histoire"),
        "!join": Command(_callback_join, "Rejoins mon armée"),
        "!find": Command(_callback_find, "Cherche un monstre à combattre"),
        #"!status": Command(_callback_status, "Affiche ton statut"),
        "!fight": Command(_callback_fight, "Lance un combat"),
    }

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
            try:
                self.commands[message].callback(self, e.target, None)
            except KeyError:
                self.connection.privmsg(e.target, f"Commande inconnue : {message}")
        return


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
    bot.start()


if __name__ == "__main__":
    main()
