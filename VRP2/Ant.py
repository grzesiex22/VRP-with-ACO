import random

from VRP2.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.vehicles = []

    # def build_route(self, pheromone, alpha, beta):
    #
    #     time = self.problem.time_matrix_seconds
    #     unvisited = [node for node in self.problem.nodes if node.id != 0]
    #     self.vehicles = []
    #     depot = self.problem.nodes[0]
    #
    #     def choose_next_node():
    #         probs = []
    #
    #         for node in unvisited:
    #
    #             tau = pheromone[current.id][node.id] ** alpha
    #             eta = (1 / time[current.id][node.id]) ** beta
    #
    #             probs.append(tau * eta)
    #
    #         total = sum(probs)
    #         probs = [p / total for p in probs]
    #
    #         return random.choices(unvisited, probs)[0]
    #
    #     vehicle_idx = 0
    #     num_vehicles = len(self.problem.vehicles)
    #
    #     while unvisited:
    #         vehicle = self.problem.vehicles[vehicle_idx % num_vehicles].__copy__()
    #         vehicle_idx += 1
    #
    #         vehicle.routes.append(depot)
    #         current = depot
    #
    #         while unvisited:
    #             next_node = choose_next_node()
    #
    #             if (vehicle.capacity is not None and
    #                     vehicle.filling + next_node.demand <= vehicle.capacity):
    #                 vehicle.filling += next_node.demand
    #             else:
    #                 break
    #
    #             vehicle.routes.append(next_node)
    #             unvisited.remove(next_node)
    #             current = next_node
    #
    #         vehicle.routes.append(depot)
    #         self.vehicles.append(vehicle)

    def build_route(self, pheromone, alpha, beta):
        time_matrix = self.problem.time_matrix_seconds
        unvisited = [node for node in self.problem.nodes if node.id != 0]
        self.vehicles = []
        depot = self.problem.nodes[0]

        num_vehicles = len(self.problem.vehicles)
        v_idx = 0

        while unvisited and v_idx < num_vehicles:
            vehicle = self.problem.vehicles[v_idx].__copy__()
            v_idx += 1

            current = depot
            vehicle.routes = [depot]
            vehicle.filling = 0

            while unvisited:
                # 1. Szukamy dostępnych klientów (którzy wejdą na auto)
                candidates = []
                probs = []
                for node in unvisited:
                    if vehicle.filling + node.demand <= vehicle.capacity:
                        tau = pheromone[current.id][node.id] ** alpha
                        eta = (1 / (time_matrix[current.id][node.id])) ** beta
                        candidates.append(node)
                        probs.append(tau * eta)

                if not candidates:
                    break

                # 2. Wybieramy klienta
                total = sum(probs)
                p = [prob / total for prob in probs]
                next_node = random.choices(candidates, p)[0]

                # 3. DODAJEMY KLIENTA (To musi być przed ewentualnym breakiem!)
                vehicle.filling += next_node.demand
                vehicle.routes.append(next_node)
                unvisited.remove(next_node)  # Klient znika z globalnej listy
                current = next_node

                # 4. DECYZJA O PRZERWANIU
                if len(unvisited) > 0 and v_idx + 1 < num_vehicles:

                    # A. Szansa losowa (eksploracja)
                    stop_chance = 0.1

                    if random.random() < stop_chance:
                        break

            # Koniec trasy pojazdu - zawsze wraca do bazy
            vehicle.routes.append(depot)
            self.vehicles.append(vehicle)
