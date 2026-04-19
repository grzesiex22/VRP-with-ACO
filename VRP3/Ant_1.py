import random

import numpy as np

from VRP3.VRP import VRP


class Ant:

    def __init__(self, problem: VRP):
        self.problem = problem
        self.gtr = []
        self.cost = 0

        self.demands = np.array([n.demand for n in problem.nodes])

    def build_route(self, scores_matrix):
        """
        scores_matrix: Macierz (Pheromone^alpha * Eta^beta) obliczona w klasie ACO
        """
        n_nodes = len(self.problem.nodes)
        depot_id = 0

        # 1. Przygotowanie danych
        remaining_clients = set(range(1, n_nodes))
        vehicle_count = len(self.problem.vehicles)

        current_v_idx = 0

        self.gtr = [self.problem.nodes[depot_id]]
        current_id = depot_id

        while remaining_clients:
            candidates_ids = []

            # --- ID pozostałych klientów ---
            for cid in remaining_clients:
                candidates_ids.append(cid)

            # DODAJEMY DEPOT JAKO NORMALNEGO KANDYDATA
            if current_id != depot_id and current_v_idx < vehicle_count - 1:
                candidates_ids.append(depot_id)

            # Decyzja co robimy:
            if not candidates_ids:
                # Brak aut lub utknięcie -> dodaj resztę klientów (kara w cost) i wyjdź
                self.gtr.extend([self.problem.nodes[cid] for cid in remaining_clients])
                break
            else:
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
            else:
                # Odjęcie ładunku i usunięcie klienta
                remaining_clients.remove(next_id)

            current_id = next_id

        # Zawsze kończymy w bazie
        if self.gtr[-1].id != 0:
            self.gtr.append(self.problem.nodes[depot_id])

    # def build_route(self, pheromone_alpha_matrix, eta_matrix):
    #
    #     depot = self.problem.nodes[0]
    #     self.gtr = [depot]
    #     current = depot
    #
    #     unvisited = [node for node in self.problem.nodes if node.id != 0]
    #     vehicle_count = len(self.problem.vehicles)
    #
    #     for _ in range(vehicle_count - 1):
    #         unvisited.append(depot)
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
    #             self.gtr.append(next_node)
    #             unvisited.remove(next_node)
    #             current = next_node
    #
    #     # Zawsze kończymy w bazie
    #     if self.gtr[-1].id != 0:
    #         self.gtr.append(depot)
    #
