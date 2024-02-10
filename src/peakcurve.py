from utils import *
from random import random, uniform

### If you describe yourself as a 'mathematician' close this file immediately
### You have been warned

#This class describes a "triangle pointing upward" curve, like a '^' shape, and is formed by 2 linear function.
#It's goal is to behave mostly like a normal curve, but with linear grownth and well defined 0 values as 'start' en 'end', peaking at 'peak' with 'peak_value'.
class PeakCurve():
    random_max_draw : int = 100000

    def __init__(self, start, peak, end, peak_value = 1) -> None:
        #Explicitely allow start == peak and peak == end, for single side grownth
        if start > peak or peak > end:
            raise ValueError
        if peak_value < 0 or peak_value > 1:
            raise ValueError
        self.peak = peak
        self.start = start
        self.end = end
        self.peak_value = peak_value

    def get_probability(self, value) -> float:
        if value < self.start or value > self.end:
            #Outside of bounds, no chance at all
            return 0
        if value == self.peak:
            #Avoid asymptotic behaviors in case start == peak or peak == end
            return self.peak_value
        elif value < self.peak:
            return (self.peak_value / (self.peak - self.start)) * value - (self.start /(self.peak - self.start) * self.peak_value)
        else:
            return -(self.peak_value / (self.end - self.peak)) * value + (self.end /(self.end - self.peak) * self.peak_value)

    def random_in_bounds(self):
        return uniform(self.start, self.end)

    def draw_at(self, value):
        rand = random()
        prob = self.get_probability(value)
        ret = rand < prob
        trace(f"Drew '{rand:.3f}' against p(x)='{prob:.3f}', with x = {value:.3f} and x ∈ [{self.start};{self.end}] & x-peak = {self.peak} : {str(ret)}")
        return ret

    def draw(self) -> float:
        for i in range(PeakCurve.random_max_draw):
            value = self.random_in_bounds()
            if self.draw_at(value):
                return value - self.start
        trace("Can't find a value in curve, check your curve values immediately")
        return 0
