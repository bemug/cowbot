from cowbot.peakcurve import *


class DownCurve(PeakCurve):
    def __init__(self, end: int) -> None:
        super().__init__(0, 0, end)
