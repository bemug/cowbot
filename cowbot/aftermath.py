from typing import Any

class Aftermath():
    #TODO either foe or player for source and target
    def __init__(self, source: Any, target: Any, damage: int, armor: int, critical: int, miss: int, hit: int, old_hp: int, rival) -> None:
        self.source = source
        self.target = target
        self.damage = damage
        self.armor = armor
        self.critical = critical
        self.miss = miss
        self.hit = hit
        self.old_hp = old_hp
        self.rival = rival
