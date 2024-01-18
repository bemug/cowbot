class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.exp = 1 #Level 1
        self.foe_exp = self.exp
        self.hp = self.get_max_hp()

    def get_level(self) -> int:
        return int(self.exp ** (1. / 3))

    def get_damage(self) -> int:
        return 4 + self.get_level()

    def get_max_hp(self) -> int:
        return 14 + self.get_level()

    def get_max_exp(self) -> int:
        return pow((self.get_level() + 1), 3)

    def __str__(self):
        return self.name.capitalize()

    def no_hl_str(self) -> str:
        #Insert this 0 width whitespace to avoid highlighting people: ​
        #See https://blanktext.net/
        s: str = self.__str__()
        return s[:1] + '​' + s[1:]

    def is_dead(self):
        return self.hp <= 0
