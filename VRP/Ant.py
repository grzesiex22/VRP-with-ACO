import random


class Ant:

    def __init__(self, problem):
        self.problem = problem
        self.routes = []

    def build_route(self, pheromone, alpha, beta):

        dist = self.problem.distance_matrix()

        unvisited = [node for node in self.problem.nodes if node.id != 0]
        self.routes = []

        def choose_next_node():
            probs = []

            for node in unvisited:
                tau = pheromone[current.id][node.id] ** alpha
                eta = (1 / dist[current.id][node.id]) ** beta

                probs.append(tau * eta)

            total = sum(probs)
            probs = [p / total for p in probs]

            return random.choices(unvisited, probs)[0]

        while unvisited:

            route = [0]  # DEPOT
            current = self.problem.nodes[0]
            current_capacity = 0

            while unvisited:
                next_node = choose_next_node()

                if (self.problem.max_capacity is not None and
                        current_capacity + next_node.demand <= self.problem.max_capacity):
                    current_capacity += next_node.demand
                else:
                    break

                route.append(next_node.id)
                unvisited.remove(next_node)
                current = next_node

            route.append(0)
            self.routes.append(route)
