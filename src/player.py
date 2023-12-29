class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.level = 1
        self.damage = 25
        self.max_hp = 100
        self.hp = self.max_hp
        self.max_exp = 10
        self.exp = self.max_exp

    def __str__(self):
        return self.name.capitalize()

    def is_dead(self):
        return self.hp <= 0
