

class Node:
    def __init__(self, id, x, y, d=0, t0=0, t1=1, p0=0, p1=0):
        self.id = id
        self.x = x  # pozycja X
        self.y = y  # pozycja Y
        self.demand = d  # zapotrzebowanie
        self.time_window = [t0, t1]
        self.penalty = [p0, p1]
