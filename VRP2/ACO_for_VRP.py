from datetime import datetime, timedelta

from VRP2.Ant import Ant
from VRP2.VRP import VRP


class ACO_for_VRP:

    def __init__(self, problem: VRP, ants=20, iterations=100):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.pheromone = [[1]*n for _ in range(n)]

        self.alpha = 1
        self.beta = 2
        self.evaporation = 0.5


    def route_cost(self, route):

        current_time_s = 0.0
        total_penalty_s = 0.0

        time_matrix = self.problem.time_matrix_seconds

        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]

            current_time_s += time_matrix[a.id][b.id]

            if current_time_s > b.time_window_s[1]:
                total_penalty_s += b.penalty_s[1]
                current_time_s += b.penalty_s[1]

            elif current_time_s < b.time_window_s[0]:
                wait_time = b.time_window_s[0] - current_time_s
                current_time_s += wait_time + b.penalty_s[0]
                total_penalty_s += b.penalty_s[0]

        return current_time_s


    def solution_cost(self, routes):

        total_time = 0.0

        for route in routes:
            total_time = self.route_cost(route)

        return total_time

    def evaporate(self):

        n = len(self.pheromone)

        for i in range(n):
            for j in range(n):
                self.pheromone[i][j] *= (1 - self.evaporation)

    def update_pheromone(self, ants):

        n = len(self.pheromone)

        # parowanie feromonu
        for i in range(n):
            for j in range(n):
                self.pheromone[i][j] *= (1 - self.evaporation)

        # dodanie nowych feromonów
        for ant in ants:

            for route in ant.routes:
                cost = self.route_cost(route)

                for i in range(len(route) - 1):
                    a = route[i]
                    b = route[i + 1]

                    self.pheromone[a.id][b.id] += 1 / cost
                    self.pheromone[b.id][a.id] += 1 / cost

    def run(self):

        best_routes = None
        best_cost = float("inf")

        for i in range(self.iterations):
            print(f"{i}")

            ants = [Ant(self.problem) for _ in range(self.ants)]

            for ant in ants:

                ant.build_route(self.pheromone, self.alpha, self.beta)

                cost = self.solution_cost(ant.routes)

                if cost < best_cost:
                    best_cost = cost
                    best_routes = ant.routes

            self.update_pheromone(ants)

        return best_routes, best_cost
