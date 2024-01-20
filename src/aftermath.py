from typing import Any

class Aftermath():
    #TODO either indian or player for source and target
    def __init__(self, source: Any, target: Any, damage: int) -> None:
        self.source = source
        self.target = target
        self.damage = damage
