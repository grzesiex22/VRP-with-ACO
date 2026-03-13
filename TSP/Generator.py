import random
from TSP.Node import Node


class Generator:

    def __init__(self, x0=0, x1=100, y0=0, y1=100, n=20):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.n = n

    def generate(self):
        nodes = []

        for i in range(self.n):
            x = random.randint(self.x0, self.x1)
            y = random.randint(self.y0, self.y1)

            nodes.append(Node(i, x, y))

        return nodes



