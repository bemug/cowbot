from cowbot.item import *


class Consumable(Item):

    def __init__(self, name, heal):
        super().__init__(name)
        self.heal = heal
