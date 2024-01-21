class Character:
    def __str__(self):
        return self.name.capitalize()

    def no_hl_str(self) -> str:
        #Insert this 0 width whitespace to avoid highlighting people: ​
        #See https://blanktext.net/
        s: str = self.__str__()
        return s[:1] + '​' + s[1:]

    def get_damage(self) -> int:
        return self.base_damage + self.get_level()

    def get_max_hp(self) -> int:
        return self.base_hp + self.get_level()

    def is_dead(self):
        return self.hp <= 0
