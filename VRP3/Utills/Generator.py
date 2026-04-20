import random
from VRP3.Problem.Node import Node
from datetime import datetime, timedelta
from VRP3.Problem.Vehicle import Vehicle


class Generator:

    def __init__(self, x0=0, x1=100, y0=0, y1=100, d0=100, d1=1000, t0=0, t1=20, s0=0, s1=0, n=20, seed=None):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.d0 = d0
        self.d1 = d1
        self.t0 = t0
        self.t1 = t1
        self.s0 = s0
        self.s1 = s1

        self.n = n

        if seed:
            random.seed(seed)

    def generate(self):

        i = 0
        nodes = []
        vehicles = []
        positions = set()
        start_day = datetime(2000, 1, 1, 0, 0)

        total_demand = 0

        while len(nodes) < self.n:
            x = random.randint(self.x0, self.x1)
            y = random.randint(self.y0, self.y1)

            if i == 0:
                x = self.x0 + (self.x1 - self.x0)/2
                y = self.y0 + (self.y1 - self.y0)/2
                d = 0
                s = 0
                hour1 = 0
                hour2 = 1
                p0 = timedelta(minutes=0)
                p1 = timedelta(minutes=0)
            else:
                d = random.randint(self.d0, self.d1)
                total_demand += d
                s = random.randint(self.s0, self.s1)
                hour1 = random.randint(self.t0, self.t1)
                hour2 = random.randint(1, self.t1 - self.t0) + self.t0
                p0 = timedelta(minutes=20)
                p1 = timedelta(minutes=30)

            t0 = datetime(2000, 1, 1, min(hour1, hour2), 0)  # 22:00
            t1 = datetime(2000, 1, 1, max(hour1, hour2), 0)  # 22:00

            service = timedelta(minutes=s)

            if (x, y) not in positions:
                positions.add((x, y))
                nodes.append(Node(i, x, y, d, t0=t0, t1=t1, p0=p0, p1=p1, service=service, start_day=start_day))
                i += 1

        # Create vehicles
        i = 0
        total_capacity = 0

        while total_capacity < 1.2 * total_demand:
            capacity = random.choice([300, 500, 700])
            total_capacity += capacity

            vehicles.append(Vehicle(id=i, capacity=capacity))
            i += 1

        return nodes, vehicles
