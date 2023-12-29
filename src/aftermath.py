from typing import Any

class Aftermath():
    #TODO either indian or player for source and target
    def __init__(self, source: Any, target: Any, from_hp: int, to_hp: int) -> None:
        self.players: List[Player] = []
        self.source = source
        self.target = target
        self.from_hp = from_hp
        self.to_hp = to_hp
