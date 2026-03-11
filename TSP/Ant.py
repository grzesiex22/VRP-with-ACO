import random


class Ant:

    def __init__(self, problem):
        self.problem = problem
        self.route = []

    def build_route(self, pheromone, alpha, beta):

        nodes = self.problem.nodes
        dist = self.problem.distance_matrix()

        unvisited = list(range(1, len(nodes)))
        route = [0]

        current = 0

        while unvisited:

            probs = []

            for node in unvisited:

                tau = pheromone[current][node] ** alpha
                eta = (1 / dist[current][node]) ** beta

                probs.append(tau * eta)

            total = sum(probs)
            probs = [p/total for p in probs]

            next_node = random.choices(unvisited, probs)[0]

            route.append(next_node)
            unvisited.remove(next_node)
            current = next_node

        route.append(0)

        self.route = route