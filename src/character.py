class Character:
    level_up_speed = 4
    exp_multiplier = 100

    def __init__(self):
        self.level = 1
        self.exp = 0

    def __str__(self):
        return self.name.capitalize()

    def no_hl_str(self) -> str:
        #Insert this 0 width whitespace to avoid highlighting people: ​
        #See https://blanktext.net/
        s: str = self.__str__()
        return s[:1] + '​' + s[1:]

    def get_damage(self) -> int:
        return self.base_damage + self.level

    def get_max_hp(self) -> int:
        return self.base_hp + self.level

    def is_dead(self):
        return self.hp <= 0

    def get_max_exp(self) -> int:
        return int(pow((self.level + 1), 3) / Character.level_up_speed * self.__class__.scale_factor * Character.exp_multiplier)

    def add_exp(self, xp: int) -> int:
        old_level: int = self.level
        self.exp += xp
        while self.exp > self.get_max_exp():
            self.exp -= self.get_max_exp()
            self.level += 1
        return self.level - old_level
