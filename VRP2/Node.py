from datetime import datetime, timedelta


class Node:
    def __init__(self, id, x, y, d=0,
                 t0: datetime = 0, t1: datetime = 1,
                 p0: timedelta = 0, p1: timedelta = 0,
                 start_day: datetime = None):
        self.id = id
        self.x = x  # pozycja X
        self.y = y  # pozycja Y
        self.demand = d  # zapotrzebowanie

        self.time_window = [t0, t1]
        self.time_window_s = [(t0 - start_day).total_seconds(), (t1 - start_day).total_seconds()]

        self.penalty = [p0, p1]

        self.penalty_s = [p0.total_seconds() if isinstance(p0, timedelta) else p0,
                          p1.total_seconds() if isinstance(p1, timedelta) else p1]
