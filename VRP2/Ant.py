import random

from VRP2.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.vehicles = []

    def build_route(self, pheromone, alpha, beta):

        time = self.problem.time_matrix_seconds

        unvisited = [node for node in self.problem.nodes if node.id != 0]
        self.vehicles = []
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

        id = 0
        N = len(self.problem.vehicles)

        while unvisited:
            vehicle = self.problem.vehicles[id % N].__copy__()
            id += 1

            vehicle.routes.append(starting_node)
            current = starting_node

            while unvisited:
                next_node = choose_next_node()

                if (vehicle.capacity is not None and
                        vehicle.filling + next_node.demand <= vehicle.capacity):
                    vehicle.filling += next_node.demand
                else:
                    break

                vehicle.routes.append(next_node)
                unvisited.remove(next_node)
                current = next_node

            vehicle.routes.append(starting_node)
            self.vehicles.append(vehicle)
