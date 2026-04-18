import random

from VRP3.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.gtr = []
        self.cost = 0

    def build_route(self, pheromone_alpha_matrix, eta_matrix):

        depot = self.problem.nodes[0]
        self.gtr = [depot]
        current = depot

        unvisited = [node for node in self.problem.nodes if node.id != 0]
        vehicle_count = len(self.problem.vehicles)

        for _ in range(vehicle_count - 1):
            unvisited.append(depot)

        # zamiast or-tools algorytm greedy albo benchmarki
        while unvisited:
            candidates = []
            probs = []

            for node in unvisited:
                # print(f"node: {node.id}, current: {current.id}, unvisted: {unvisited[0]}")
                if current.id == node.id:
                    # print(f"pomijamy1")
                    continue

                probabilities = pheromone_alpha_matrix[current.id, node.id] * eta_matrix[current.id, node.id]

                candidates.append(node)
                probs.append(probabilities)

            # 4. AWARIA (Zabezpieczenie z random.choices)
            if not candidates:
                self.gtr.extend(unvisited)
                break
            else:
                total = sum(probs)
                p_dist = [p / total for p in probs]
                next_node = random.choices(candidates, p_dist)[0]

                self.gtr.append(next_node)
                unvisited.remove(next_node)
                current = next_node

        # Zawsze kończymy w bazie
        if self.gtr[-1].id != 0:
            self.gtr.append(depot)

