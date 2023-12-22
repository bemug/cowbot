import pydle
import time
from game import *
from indian import *
from utils import *


class Command():
    def __init__(self, callback, help_message):
        self.callback = callback
        self.help_message = help_message


class Cowbot(pydle.Client):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dungeon = Dungeon()

    async def _callback_help(self, target, source, *argv):
        for name in self.commands:
            await self.message(target, name + " : " + self.commands[name].help_message)

    async def _callback_pitch(self, target, source, *argv):
        await self.message(target, "pitch")

    async def _callback_join(self, target, source, *argv):
        self.dungeon.add_player(source)
        await self.message(target, f"join {source}.")

    async def _callback_find(self, target, source, *argv):
        self.dungeon.generate_monster()
        await self.message(target, f"find {self.dungeon.monster.name} {self.dungeon.monster.adjective}.")

    async def _callback_fight(self, target, source, *argv):
        while self.dungeon.monster.is_alive():
            self.dungeon.fight()
            if self.dungeon.turn == Turn.PLAYER:
                log = "⚔ {} frappe {} {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
                        self.dungeon.player.name,
                        self.dungeon.monster.name,
                        self.dungeon.monster.adjective,
                        colors["red"],
                        self.dungeon.player.damage,
                        colors["reset"], colors["green"],
                        "???",
                        colors["reset"], colors["green"],
                        self.dungeon.monster.hp,
                        colors["reset"],
                    )
            else:
                log = "⚔ {} {} frappe {} pour {}{} DMG{} ({}{} PV{} → {}{} PV{}).".format(
                        self.dungeon.monster.name,
                        self.dungeon.monster.adjective,
                        self.dungeon.player.name,
                        colors["red"],
                        self.dungeon.monster.damage,
                        colors["reset"], colors["green"],
                        "???",
                        colors["reset"], colors["green"],
                        self.dungeon.player.hp,
                        colors["reset"],
                    )
            await self.message(target, log)
            time.sleep(1)
        self.dungeon.clear_monster()

    commands = {
        "!help": Command(_callback_help, "Affiche cette aide"),
        "!pitch": Command(_callback_pitch, "Conte l'histoire"),
        "!join": Command(_callback_join, "Rejoins mon armée"),
        "!find": Command(_callback_find, "Cherche un monstre à combattre"),
        #"!status": Command(_callback_status, "Affiche ton statut"),
        "!fight": Command(_callback_fight, "Lance un combat"),
    }

    async def on_connect(self):
        await self.join('##donjon')

    async def on_message(self, target, source, message):
        # don't respond to our own messages, as this leads to a positive feedback loop
        if source != self.nickname:
            if message.startswith('!'):
                await self.commands[message].callback(self, target, source)

client = Cowbot('cowbot', realname='Patron du saloon')
client.run('irc.libera.chat', tls=True, tls_verify=False)
