class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.level = 1
        self.damage = 5
        self.max_hp = 25
        self.hp = self.max_hp
        self.max_exp = 10
        self.exp = 0

    def __str__(self):
        return self.name.capitalize()

    def is_dead(self):
        return self.hp <= 0
