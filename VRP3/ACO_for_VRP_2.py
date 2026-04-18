from datetime import datetime, timedelta

import numpy as np
from tqdm import tqdm
from datetime import timedelta
from colorama import Fore, Back, Style, init

from VRP3.Ant_2 import Ant

from VRP3.VRP import VRP
from VRP3.Vehicle import Vehicle

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)


class ACO_for_VRP_2:

    def __init__(self, problem: VRP, ants=20, iterations=100, alpha=1, beta=2, evaporation=0.05,
                 tau_min=0.01, tau_max=5.0):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.pheromone = np.ones((n, n))

        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation

        # ograniczenia feromonu
        self.tau_max = tau_max
        self.tau_min = tau_min

        # do szybszego odczytu potęg
        self.eta_matrix = (1.0 / (np.array(self.problem.time_matrix_seconds) + 1e-6)) ** self.beta

        # Tablice do przechowywania historii (do wykresu)
        self.history_best_overall = []  # Najlepszy koszt
        self.history_best_in_iter = []  # Najlepsze koszty każdej iteracji
        self.history_avg_in_iter = []  # Średni koszt w danej iteracj

    def chop_gtr(self, route):
        routes = []
        current_route = []

        for node in route:
            current_route.append(node)
            if node.id == 0 and len(current_route) > 1:
                routes.append(current_route)
                current_route = [node]  # Zaczynamy nową trasę od bazy

        vehicles: list[Vehicle] = []
        for idx, route in enumerate(routes):
            new_v = self.problem.vehicles[idx].__copy__()
            new_v.route = route
            vehicles.append(new_v)

        return vehicles

    def route_cost(self, route):
        current_time_s = 0.0
        time_matrix = self.problem.time_matrix_seconds

        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]

            # 1. Czas dojazdu
            current_time_s += time_matrix[a.id][b.id]

            # 2. Logika okien czasowych i kar - TYLKO dla klientów (b.id != 0)
            if b.id != 0:
                # Spóźnienie (kara dodawana do czasu)
                if current_time_s > b.time_window_s[1]:
                    current_time_s += b.penalty_s[1]

                # Czekanie na otwarcie okna
                elif current_time_s < b.time_window_s[0]:
                    current_time_s = b.time_window_s[0]

                # 3. Czas obsługi (tylko u klienta)
                current_time_s += b.service_s

        return current_time_s

    def solution_cost(self, gtr):

        total_time = 0.0

        # 1. Tniemy GTR na poszczególne trasy (dzielimy tam, gdzie jest depot ID=0)
        vehicles = self.chop_gtr(gtr)

        # 2. Liczymy koszt każdej trasy z uwzględnieniem ładowności i czasu
        all_visited_ids = set()

        for vehicle in vehicles:
            # A. Koszt czasu jednej trasy
            r_time_cost = self.route_cost(vehicle.route)

            # B. Kara za przeładowanie (Capacity)
            vehicle.filling = sum(node.demand for node in vehicle.route)
            capacity_penalty = 0
            if vehicle.filling > vehicle.capacity:  # Zakładamy równą pojemność lub bierzemy z v_obj
                # print("Przeładowanie")
                overload = vehicle.filling - vehicle.capacity
                capacity_penalty = overload * 10000  # Bardzo ciężka kara

            # total_time = max(self.route_cost(route), total_time)
            total_time += (r_time_cost + capacity_penalty)

            # C. Kolekcjonujemy ID klientów (do sprawdzenia czy wszyscy obsłużeni)
            for n in vehicle.route:
                if n.id != 0:
                    all_visited_ids.add(n.id)

        # 3. Kara za nieodwiedzenie wszystkich (Safety net) - nie wywyołuje się
        num_clients = len(self.problem.nodes) - 1
        if len(all_visited_ids) < num_clients:
            missing = num_clients - len(all_visited_ids)
            print(f"{Fore.RED}{Style.BRIGHT}  UWAGA: Nie odwiedzono wszystkich! Brakuje: {missing} klientów!{Style.RESET_ALL}")
            total_time += (num_clients - len(all_visited_ids)) * 1000

        return total_time, vehicles

    def evaporate(self):

        self.pheromone *= (1 - self.evaporation)

        # n = len(self.pheromone)
        #
        # for i in range(n):
        #     for j in range(n):
        #         self.pheromone[i][j] *= (1 - self.evaporation)

    def update_pheromone(self, ants):
        # parowanie feromonu
        self.evaporate()

        # dodanie nowych feromonów
        for ant in ants:

            ids = [node.id for node in ant.gtr]
            d_tau = 1.0 / ant.cost

            for i in range(len(ids) - 1):
                a, b = ids[i], ids[i + 1]
                self.pheromone[a, b] += d_tau
                self.pheromone[b, a] += d_tau

        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def run(self, patience=100):

        best_vehicles = None
        best_cost = float("inf")
        no_improvement_count = 0

        # Tablice do przechowywania historii (do wykresu)
        self.history_best_overall = []  # Najlepszy koszt
        self.history_best_in_iter = []  # Najlepsze koszty każdej iteracji
        self.history_avg_in_iter = []  # Średni koszt w danej iteracj

        # Tworzymy pasek postępu
        pbar = tqdm(range(self.iterations), desc="ACO Optimization", unit="it")

        for i in pbar:

            ants = [Ant(self.problem) for _ in range(self.ants)]
            pheromone_alpha = self.pheromone ** self.alpha

            found_better_in_iter = False
            iter_costs = []

            for ant in ants:

                #### tu zrównoleglić
                ant.build_route(pheromone_alpha, self.eta_matrix)

                cost, vehicles = self.solution_cost(ant.gtr)
                ant.cost = cost

                iter_costs.append(cost)

                if cost < best_cost:
                    best_cost = cost
                    best_vehicles = vehicles
                    no_improvement_count = 0
                    found_better_in_iter = True
                #### tu zrównoleglić - koniec

                # można podbijać losowo feromony gdy stagnacja

            # Zapisujemy historię
            self.history_best_overall.append(best_cost)
            self.history_avg_in_iter.append(sum(iter_costs) / len(iter_costs))
            self.history_best_in_iter.append(min(iter_costs))

            self.update_pheromone(ants)

            if not found_better_in_iter:
                no_improvement_count += 1

            # AKTUALIZACJA PASKA POSTĘPU
            pbar.set_postfix({
                "Best Cost": f"{(best_cost/60):.2f} min",
                "Stagnation": f"{no_improvement_count}/{patience}"
            })

            # Decyzja o przerwaniu
            if no_improvement_count >= patience:
                print(Fore.RED + f"\n[EARLY STOPPING]" + Style.RESET_ALL + f" Brak poprawy przez {patience} iteracji. Przerywam w iteracji {i}.")
                break

        history_data = {
            'overall': self.history_best_overall,
            'avg': self.history_avg_in_iter,
            'iter_best': self.history_best_in_iter
        }

        return best_vehicles, best_cost, history_data
