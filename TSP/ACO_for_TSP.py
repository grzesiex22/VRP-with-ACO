from TSP.Ant import Ant


class ACO_for_TSP:

    def __init__(self, problem, ants=20, iterations=100):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.pheromone = [[1]*n for _ in range(n)]

        self.alpha = 1
        self.beta = 2
        self.evaporation = 0.5

    def route_cost(self, route):

        dist = self.problem.distance_matrix()

        cost = 0

        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]

            cost += dist[a][b]

        return cost

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

            route = ant.route
            cost = self.route_cost(route)

            for i in range(len(route) - 1):
                a = route[i]
                b = route[i + 1]

                self.pheromone[a][b] += 1 / cost
                self.pheromone[b][a] += 1 / cost

    def run(self):

        best_route = None
        best_cost = float("inf")

        for _ in range(self.iterations):

            ants = [Ant(self.problem) for _ in range(self.ants)]

            for ant in ants:

                ant.build_route(self.pheromone, self.alpha, self.beta)

                cost = self.route_cost(ant.route)

                if cost < best_cost:
                    best_cost = cost
                    best_route = ant.route

            self.update_pheromone(ants)

        return best_route, best_cost