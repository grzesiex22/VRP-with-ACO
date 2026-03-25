import math
from datetime import timedelta
from VRP2.Node import Node


class VRP:

    def __init__(self, nodes: list, depot_index=0, max_capacity=None):
        self.nodes = nodes
        self.depot = nodes[depot_index]
        self.time_matrix = self.time_matrix()
        self.time_matrix_seconds = self.time_matrix_seconds()
        self.max_capacity = max_capacity

    def distance(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

    def time(self, a, b, velocity=60):
        # Tworzymy obiekt przedziału czasowego
        return timedelta(hours=self.distance(a, b) / velocity)

    def time_matrix(self):

        n = len(self.nodes)
        matrix = [[timedelta(0)] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.time(self.nodes[i], self.nodes[j])

        return matrix

    def time_matrix_seconds(self):
        n = len(self.nodes)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):  # Optymalizacja: liczymy tylko połowę macierzy

                duration = self.time(self.nodes[i], self.nodes[j])
                seconds = duration.total_seconds()

                # Wpisujemy do macierzy (symetrycznie)
                matrix[i][j] = seconds
                matrix[j][i] = seconds

        return matrix
