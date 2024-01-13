class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.exp = 0
        self.foe_exp = 0
        self.hp = self._get_max_hp()

    def _get_level(self) -> int:
        return int(self.exp ** (1. / 3))

    def _get_damage(self) -> int:
        return 5 + self._get_level()

    def _get_max_hp(self) -> int:
        return 15 + self._get_level()

    def __str__(self):
        return self.name.capitalize()

    def is_dead(self):
        return self.hp <= 0
