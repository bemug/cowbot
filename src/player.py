class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.exp = 0
        self.foe_exp = self.exp
        self.hp = self.get_max_hp()

    def get_level(self) -> int:
        return int(self.exp ** (1. / 3)) + 1

    def get_damage(self) -> int:
        return 4 + self.get_level()

    def get_max_hp(self) -> int:
        return 14 + self.get_level()

    def __str__(self):
        return self.name.capitalize()

    def is_dead(self):
        return self.hp <= 0
