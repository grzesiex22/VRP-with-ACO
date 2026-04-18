import random

from VRP3.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.gtr = []
        self.cost = 0

    def build_route(self, pheromone, alpha, beta):

        time = self.problem.time_matrix_seconds
        depot = self.problem.nodes[0]
        self.gtr = [depot]
        current = depot

        free_space = [v.capacity for v in self.problem.vehicles]
        space_idx = 0

        unvisited = [node for node in self.problem.nodes if node.id != 0]
        vehicle_count = len(self.problem.vehicles)

        # zamiast or-tools algorytm greedy albo benchmarki
        while unvisited:
            candidates = []
            probs = []

            for node in unvisited:
                # print(f"node: {node.id}, current: {current.id}, unvisted: {unvisited[0]}")
                if current.id == node.id:
                    # print(f"pomijamy1")
                    continue

                tau = pheromone[current.id][node.id] ** alpha
                eta = (1 / time[current.id][node.id]) ** beta

                candidates.append(node)
                probs.append(tau * eta)

            # 4. AWARIA (Zabezpieczenie z random.choices)
            if not candidates:
                self.gtr.extend(unvisited)
                break
            else:
                total = sum(probs)
                p_dist = [p / total for p in probs]
                next_node = random.choices(candidates, p_dist)[0]

                if next_node.demand > free_space[space_idx % len(free_space)]:
                    space_idx += 1
                    self.gtr.append(depot)

                self.gtr.append(next_node)
                free_space[space_idx % len(free_space)] -= next_node.demand
                unvisited.remove(next_node)
                current = next_node

        # Zawsze kończymy w bazie
        if self.gtr[-1].id != 0:
            self.gtr.append(depot)