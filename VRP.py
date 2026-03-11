import math


class VRP:

    def __init__(self, nodes, depot_index=0):
        self.nodes = nodes
        self.depot = nodes[depot_index]
        self.dist_matrix = self.distance_matrix()

    def distance(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

    def distance_matrix(self):

        n = len(self.nodes)
        matrix = [[0]*n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.distance(self.nodes[i], self.nodes[j])

        return matrix
