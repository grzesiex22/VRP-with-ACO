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
        vehicle_capacities = [v.capacity for v in self.problem.vehicles]
        vehicle_count = len(vehicle_capacities)

        current_v_idx = 0
        current_free_space = vehicle_capacities[current_v_idx]

        self.gtr = [self.problem.nodes[depot_id]]
        current_id = depot_id

        while remaining_clients:
            candidates_ids = []

            # --- FILTROWANIE PO POJEMNOŚCI ---
            # Sprawdzamy, którzy z nieodwiedzonych klientów zmieszczą się w obecnym aucie
            for cid in remaining_clients:
                if self.demands[cid] <= current_free_space:
                    candidates_ids.append(cid)

            # DODAJEMY DEPOT JAKO NORMALNEGO KANDYDATA
            # Jeśli jesteśmy u klienta i mamy jeszcze zapasowe auta, baza jest opcją
            if current_id != depot_id and current_v_idx < vehicle_count - 1:
                candidates_ids.append(depot_id)

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
    #     for _ in range(vehicle_count - 1):
    #         unvisited.append(depot)
    #
    #     while unvisited:
    #         candidates = []
    #         probs = []
    #
    #         for node in unvisited:
    #             # print(f"node: {node.id}, current: {current.id}, unvisted: {unvisited[0]}")
    #             if current.id == node.id:  # Nie idziemy do tego samego punktu (np. 0 -> 0)
    #                 # print(f"pomijamy1")
    #                 continue
    #
    #             # --- KLUCZOWE OGRANICZENIE ---
    #             # Nie pozwalamy mrówce wybrać klienta, który fizycznie nie wejdzie do aktualnego auta
    #             if node.id != 0 and node.demand > free_space[space_idx]:
    #                 continue
    #
    #             probabilities = pheromone_alpha_matrix[current.id, node.id] * eta_matrix[current.id, node.id]
    #
    #             candidates.append(node)
    #             probs.append(probabilities)
    #
    #         if not candidates:
    #             # Jeśli mrówka utknęła (np. klient nie mieści się w żadnym aucie),
    #             # musimy wymusić powrót do bazy, o ile mamy jeszcze jakieś auto.
    #             if current.id != 0 and space_idx < vehicle_count - 1:
    #                 # Wymuszony powrót do bazy
    #                 next_node = depot
    #             else:
    #                 # Brak opcji - kończymy trasę
    #                 self.gtr.extend([n for n in unvisited if n.id != 0])  # dodaj nieodwiedzonych dla kary w cost
    #                 break
    #         else:
    #             total = sum(probs)
    #             p_dist = [p / total for p in probs]
    #             next_node = random.choices(candidates, p_dist)[0]
    #
    #         # --- LOGIKA PRZEŁĄCZANIA POJAZDÓW ---
    #         if next_node.id == 0:
    #             # Mrówka wybrała (lub wymuszono) powrót do bazy
    #             space_idx += 1
    #             # Po powrocie do bazy nie odejmujemy demand (jest 0), przechodzimy do nowej pętli
    #         else:
    #             free_space[space_idx] -= next_node.demand
    #
    #         # --- LOGIKA ODWIEDZIN KLIENTA ---
    #         self.gtr.append(next_node)
    #         unvisited.remove(next_node)
    #         current = next_node
    #
    #     # Zawsze kończymy w bazie
    #     if self.gtr[-1].id != 0:
    #         self.gtr.append(depot)
