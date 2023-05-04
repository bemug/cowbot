import pydle

class Command():
    def __init__(self, callback, help_message):
        self.callback = callback
        self.help_message = help_message


class Gorgobot(pydle.Client):

    #Has a game, game has players

    def __init__():
        super();
        #get back game
        print("Hola");

    async def callback_help(self, target, source, *argv):
        for name in self.commands:
            await self.message(target, name + " : " + self.commands[name].help_message)

    async def callback_pitch(self, target, source, *argv):
        await self.message(target, "Ceci est mon donjon, " + source + ". Il attire moults aventuriers prêts à me voler mon butin si durement et cruellement accumulé. J'ai besoin de sbires comme vous pour renforcer mes défenses. Je serais me montrer redevable cela va se soi.")

    commands = {
        "!help": Command(callback_help, "Affiche cette aide"),
        "!pitch": Command(callback_pitch, "Conte l'histoire"),
        #"!status": Command(callback_status, "Affiche ton statut"),
        #"!battle": Command(callback_battle, "Force un combat"),
    }

    async def on_connect(self):
        await self.join('##donjon')

    async def on_message(self, target, source, message):
        # don't respond to our own messages, as this leads to a positive feedback loop
        if source != self.nickname:
            if message.startswith('!'):
                await self.commands[message].callback(self, target, source)

client = Gorgobot('gorgobot', realname='Maitre du donjon')
client.run('irc.libera.chat', tls=True, tls_verify=False)
