from pydle import Client, Source, Target # type: ignore
from time import sleep
from typing import Any, Awaitable, Callable, Coroutine
from game import *
from indian import *
from utils import *


class Command():
    def __init__(self, callback: Callable[[Cowbot, Any, Any, Any], Coroutine[Any, Any, None]], help_message: str) -> None:
        self.callback = callback
        self.help_message = help_message


class Cowbot(Client): # type: ignore
    def __init__(self, *args: str, **kwargs: int) -> None:
        super().__init__(*args, **kwargs)
        self.game = Game()

    async def _callback_help(self, target: Target, source: Source, *argv: Any) -> None:
        for name in self.commands:
            await self.message(target, name + " : " + self.commands[name].help_message)

    async def _callback_pitch(self, target: Target, source: Source, *argv: Any) -> None:
        await self.message(target, "pitch")

    async def _callback_join(self, target: Target, source: Source, *argv: Any) -> None:
        self.dungeon.add_player(source)
        await self.message(target, f"join {source}.")

    async def _callback_find(self, target: Target, source: Source, *argv: Any) -> None:
        self.dungeon.generate_indian()
        await self.message(target, f"find {self.dungeon.indian.name} {self.dungeon.indian.adjective}.")

    async def _callback_fight(self, target: Target, source: Source, *argv: Any) -> None:
        while self.dungeon.indian.is_alive():
            self.dungeon.fight()
            if self.dungeon.turn == Turn.PLAYER:
                log = "⚔ {} frappe {} {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
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
                log = "⚔ {} {} frappe {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
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
            await self.message(target, log)
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

    async def on_connect(self) -> None:
        await self.join('##donjon')

    async def on_message(self, target: Target, source: Source, message: str) -> None:
        # don't respond to our own messages, as this leads to a positive feedback loop
        if source != self.nickname:
            if message.startswith('!'):
                await self.commands[message].callback(self, target, source, None)


client = Cowbot('cowbot', realname='Patron du saloon') # type: ignore
client.run('irc.libera.chat', tls=True, tls_verify=False)
