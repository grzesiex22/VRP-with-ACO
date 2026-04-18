import random

import numpy as np

from VRP3.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.gtr = []
        self.cost = 0

        self.demands = np.array([n.demand for n in problem.nodes])

    def build_route(self, pheromone_alpha_matrix, eta_matrix):
        """
        scores_matrix: Macierz (Pheromone^alpha * Eta^beta) obliczona w klasie ACO
        """
        n_nodes = len(self.problem.nodes)
        depot_id = 0

        # 1. Przygotowanie danych
        remaining_clients = set(range(1, n_nodes))
        vehicle_capacities = [v.capacity for v in self.problem.vehicles]
        vehicle_count = len(vehicle_capacities)

        current_v_idx = 0
        current_free_space = vehicle_capacities[current_v_idx]

        scores_matrix = pheromone_alpha_matrix * eta_matrix

        self.gtr = [self.problem.nodes[depot_id]]
        current_id = depot_id

        while remaining_clients:
            candidates_ids = []

            # --- FILTROWANIE PO POJEMNOŚCI ---
            # Sprawdzamy, którzy z nieodwiedzonych klientów zmieszczą się w obecnym aucie
            for cid in remaining_clients:
                if self.demands[cid] <= current_free_space:
                    candidates_ids.append(cid)

            # Decyzja co robimy:
            if not candidates_ids:
                # Jeśli nikt się nie mieści, a mamy jeszcze auta -> wracamy do bazy
                if current_id != depot_id and current_v_idx < vehicle_count - 1:
                    next_id = depot_id
                else:
                    # Brak aut lub utknięcie -> dodaj resztę klientów (kara w cost) i wyjdź
                    self.gtr.extend([self.problem.nodes[cid] for cid in remaining_clients])
                    break
            else:
                # Jeśli jesteśmy w trasie, możemy też rozważyć powrót do bazy "z wyboru"
                # (Opcjonalne, ale w VRP4 miałeś powrót tylko gdy brak miejsca lub candidates)
                # Pobieramy wagi tylko dla dozwolonych kandydatów
                weights = scores_matrix[current_id, candidates_ids]

                # Losowanie
                next_id = random.choices(candidates_ids, weights=weights)[0]

            # --- AKTUALIZACJA STANU ---
            next_node = self.problem.nodes[next_id]
            self.gtr.append(next_node)

            if next_id == depot_id:
                # Przesiadka na nowe auto
                current_v_idx += 1
                current_free_space = vehicle_capacities[current_v_idx]
            else:
                # Odjęcie ładunku i usunięcie klienta
                current_free_space -= self.demands[next_id]
                remaining_clients.remove(next_id)

            current_id = next_id

        # Zawsze kończymy w bazie
        if self.gtr[-1].id != 0:
            self.gtr.append(self.problem.nodes[depot_id])

    # def build_route(self, pheromone_alpha_matrix, eta_matrix):
    #
    #     time = self.problem.time_matrix_seconds
    #     depot = self.problem.nodes[0]
    #     self.gtr = [depot]
    #     current = depot
    #
    #     free_space = [v.capacity for v in self.problem.vehicles]
    #     space_idx = 0
    #
    #     unvisited = [node for node in self.problem.nodes if node.id != 0]
    #     vehicle_count = len(self.problem.vehicles)
    #
    #     # zamiast or-tools algorytm greedy albo benchmarki
    #     while unvisited:
    #         candidates = []
    #         probs = []
    #
    #         for node in unvisited:
    #             # print(f"node: {node.id}, current: {current.id}, unvisted: {unvisited[0]}")
    #             if current.id == node.id:
    #                 # print(f"pomijamy1")
    #                 continue
    #
    #             probabilities = pheromone_alpha_matrix[current.id, node.id] * eta_matrix[current.id, node.id]
    #
    #             candidates.append(node)
    #             probs.append(probabilities)
    #
    #         # 4. AWARIA (Zabezpieczenie z random.choices)
    #         if not candidates:
    #             self.gtr.extend(unvisited)
    #             break
    #         else:
    #             total = sum(probs)
    #             p_dist = [p / total for p in probs]
    #             next_node = random.choices(candidates, p_dist)[0]
    #
    #             if next_node.demand > free_space[space_idx % len(free_space)]:
    #                 space_idx += 1
    #                 self.gtr.append(depot)
    #
    #             self.gtr.append(next_node)
    #             free_space[space_idx % len(free_space)] -= next_node.demand
    #             unvisited.remove(next_node)
    #             current = next_node
    #
    #     # Zawsze kończymy w bazie
    #     if self.gtr[-1].id != 0:
    #         self.gtr.append(depot)
