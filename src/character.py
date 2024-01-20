class Character:
    def no_hl_str(self) -> str:
        #Insert this 0 width whitespace to avoid highlighting people: ​
        #See https://blanktext.net/
        s: str = self.__str__()
        return s[:1] + '​' + s[1:]

    def is_dead(self):
        return self.hp <= 0
