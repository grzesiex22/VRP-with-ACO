import random
from VRP.Node import Node


class Generator:

    def __init__(self, x0=0, x1=100, y0=0, y1=100, d0=100, d1=1000, n=20, seed=None):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.d0 = d0
        self.d1 = d1

        self.n = n

        if seed:
            random.seed(seed)

    def generate(self):

        i = 0
        nodes = []
        positions = set()

        while len(nodes) < self.n:
            x = random.randint(self.x0, self.x1)
            y = random.randint(self.y0, self.y1)

            if i == 0:
                d = 0
            else:
                d = random.randint(self.d0, self.d1)

            if (x, y) not in positions:
                positions.add((x, y))
                nodes.append(Node(i, x, y, d))
                i += 1

        return nodes