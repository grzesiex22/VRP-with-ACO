import random

from VRP2.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.routes = []

    def build_route(self, pheromone, alpha, beta):

        time = self.problem.time_matrix_seconds

        unvisited = [node for node in self.problem.nodes if node.id != 0]
        self.routes = []
        starting_node = self.problem.nodes[0]

        def choose_next_node():
            probs = []

            for node in unvisited:

                tau = pheromone[current.id][node.id] ** alpha
                eta = (1 / time[current.id][node.id]) ** beta

                probs.append(tau * eta)

            total = sum(probs)
            probs = [p / total for p in probs]

            return random.choices(unvisited, probs)[0]

        while unvisited:

            current = starting_node
            current_capacity = 0
            route = [current]  # DEPOT

            while unvisited:
                next_node = choose_next_node()

                if (self.problem.max_capacity is not None and
                        current_capacity + next_node.demand <= self.problem.max_capacity):
                    current_capacity += next_node.demand
                else:
                    break

                route.append(next_node)
                unvisited.remove(next_node)
                current = next_node

            route.append(starting_node)
            self.routes.append(route)
