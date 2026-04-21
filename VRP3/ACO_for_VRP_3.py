import numpy as np
from tqdm import tqdm
from colorama import Fore, Style, init
import random

from VRP3.Ant_3 import Ant
from VRP3.Problem.VRP import VRP
from VRP3.Problem.Vehicle import Vehicle

import sys

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)


class ACO_for_VRP_3:

    def __init__(self, problem: VRP, ants=20, iterations=100, alpha=1, beta=2, evaporation=0.05, patience=1000,
                 q_pheromone=100.0, tau_min=0.01, tau_max=5.0):
        self.problem = problem
        self.ants = ants
        self.iterations = iterations
        self.patience = patience

        n = len(problem.nodes)
        self.phr_max_lvl = 0.8
        self.phr_base_lvl = 0.3
        self.phr_min_lvl = 0.05
        self.phr_intensifier = 0.1
        self.pheromone = [[self.phr_base_lvl]*n for _ in range(n)]

        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        self.Q_pheromone = q_pheromone

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

        # 1. Rozbijamy GTR na poszczególne trasy (pomiędzy zerami)
        for node in route:
            current_route.append(node)
            if node.id == 0 and len(current_route) > 1:
                routes.append(current_route)
                current_route = [node]  # Zaczynamy nową trasę od bazy

        vehicles: list[Vehicle] = []
        # 2. Przypisujemy trasy do pojazdów (tyle, ile mamy tras)
        for idx, r in enumerate(routes):
            if idx < len(self.problem.vehicles):
                new_v = self.problem.vehicles[idx].__copy__()
                new_v.route = r
                # Opcjonalnie przelicz filling, jeśli klasa Vehicle tego nie robi w locie
                new_v.filling = sum(n.demand for n in r)
                vehicles.append(new_v)

        # 3. Dodajemy puste pojazdy z floty, które nie zostały użyte
        num_used = len(vehicles)
        num_total = len(self.problem.vehicles)

        if num_used < num_total:
            for i in range(num_used, num_total):
                empty_v = self.problem.vehicles[i].__copy__()
                # Pusta trasa to wyjazd i natychmiastowy powrót do bazy
                empty_v.route = [self.problem.nodes[0], self.problem.nodes[0]]
                empty_v.filling = 0
                vehicles.append(empty_v)

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
            vehicle.duration = r_time_cost

            # B. Kara za przeładowanie (Capacity)
            vehicle.filling = sum(node.demand for node in vehicle.route)
            capacity_penalty = 0
            if vehicle.filling > vehicle.capacity:  # Zakładamy równą pojemność lub bierzemy z v_obj
                # print("Przeładowanie")
                overload = vehicle.filling - vehicle.capacity
                capacity_penalty = overload * 10_000  # Bardzo ciężka kara

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

        n = len(self.pheromone)

        for i in range(n):
            for j in range(n):
                self.pheromone[i][j] *= (1 - self.evaporation)

    def update_one(self, gtr):
        vehicles = self.solution_cost(gtr)[1]

        for vehicle in vehicles:
            cost = vehicle.duration
            route = vehicle.route

            for i in range(len(vehicle.route) - 1):
                a = route[i]
                b = route[i + 1]

                self.pheromone[a.id][b.id] += cost / self.eta_matrix[a.id][b.id]
                self.pheromone[b.id][a.id] += cost / self.eta_matrix[b.id][a.id]

                if self.pheromone[a.id][b.id] > self.phr_max_lvl:
                    self.pheromone[a.id][b.id] = self.phr_max_lvl
                    self.pheromone[b.id][a.id] = self.phr_max_lvl

    def update_pheromone(self, ants):
        for ant in ants:
            self.update_one(ant.gtr)

    def reset_phermones(self, best_vehicles):
        n = len(self.pheromone)

        # 1. Reset całej macierzy do poziomu bazowego
        new_pheromone = [
            [self.phr_base_lvl for _ in range(n)]
            for _ in range(n)
        ]

        # 2. Zachowanie feromonów najlepszej trasy
        for vehicle in best_vehicles:
            route = [node.id for node in vehicle.route]

            for i in range(len(route) - 1):
                a = route[i]
                b = route[i + 1]

                # kopiujemy feromon z poprzedniej macierzy
                new_pheromone[a][b] = self.pheromone[a][b]
                new_pheromone[b][a] = self.pheromone[b][a]

        # 3. Podmiana macierzy
        self.pheromone = new_pheromone

    def intensify_phermones(self):
        for row in self.pheromone:
            for phr in row:
                if phr < self.phr_min_lvl:
                    phr += self.phr_intensifier

    def two_opt(self, gtr, eps=10):
        n = len(gtr)

        while True:
            p1 = random.randint(1, n - 2)
            low = max(1, p1 - eps)
            high = min(n - 1, p1 + eps)
            p2 = random.randint(low, high)

            if p1 == p2:
                continue

            if p2 < p1:
                p1, p2 = p2, p1

            # sprawdź czy w środku nie ma depotu
            if any(node.id == 0 for node in gtr[p1:p2+1]):
                continue

            break

        gtr[p1:p2] = reversed(gtr[p1:p2])

    def local_swap(self, gtr, eps=3):
        n = len(gtr)

        while True:
            p1 = random.randint(1, n - 2)
            low = max(1, p1 - eps)
            high = min(n - 1, p1 + eps)
            p2 = random.randint(low, high)

            if p1 == p2:
                continue

            if p2 < p1:
                p1, p2 = p2, p1

            # sprawdź czy w środku nie ma depotu
            if any(node.id == 0 for node in gtr[p1:p2+1]):
                continue

            break

        gtr[p1], gtr[p2] = gtr[p2], gtr[p1]

    def run(self):

        best_gtr = []
        best_vehicles = None
        best_cost = float("inf")

        no_improvement_count = 0

        used_vehicles_count = 0
        vehicles_count = len(self.problem.vehicles)

        num_best = int(self.ants * 1)
        best_iters = []
        best_iter_costs = [sys.maxsize] * num_best

        best_iter = None
        best_iter_cost = sys.maxsize

        # Tablice do przechowywania historii (do wykresu)
        self.history_best_overall = []  # Najlepszy koszt
        self.history_best_in_iter = []  # Najlepsze koszty każdej iteracji
        self.history_avg_in_iter = []  # Średni koszt w danej iteracj

        # Tworzymy pasek postępu
        pbar = tqdm(range(self.iterations), desc="ACO 3", unit="it")

        for i in pbar:

            ants = [Ant(self.problem) for _ in range(self.ants)]

            found_better_in_iter = False
            iter_costs = []

            for ant in ants:
                #### tu zrównoleglić
                ant.build_route(self.pheromone, self.alpha, self.eta_matrix)

                # for i in range(5):
                #     self.local_swap(ant.gtr)
                # if random.random() < 0.3:
                #     self.two_opt(ant.gtr, 10)

                cost, vehicles = self.solution_cost(ant.gtr)
                ant.cost = cost

                iter_costs.append(cost)

                # BEST IN ITERATION
                if cost < best_iter_cost:
                    best_iter_cost = cost
                    best_iter = ant.gtr

                # best globally
                if cost < best_cost:
                    best_cost = cost
                    best_gtr = ant.gtr
                    best_vehicles = vehicles
                    used_vehicles_count = sum(1 for v in best_vehicles if len(v.route) > 2)
                    no_improvement_count = 0
                    found_better_in_iter = True
                #### tu zrównoleglić - koniec

                # można podbijać losowo feromony gdy stagnacja

            # Zapisujemy historię
            self.history_best_overall.append(best_cost)
            self.history_avg_in_iter.append(sum(iter_costs) / len(iter_costs))
            self.history_best_in_iter.append(min(iter_costs))

            self.evaporate()

            self.update_one(best_iter)
            self.update_one(best_gtr)

            if not found_better_in_iter:
                no_improvement_count += 1

            # AKTUALIZACJA PASKA POSTĘPU
            pbar.set_postfix({
                "Best": f"{(best_cost/60):.2f} min",
                "Veh": f"{used_vehicles_count}/{vehicles_count}",
                "Evap": f"{self.evaporation:.2f}",
                "Alfa": f"{self.alpha:.1f}",
                "Beta": f"{self.beta:.1f}",
                "Stagnation": f"{no_improvement_count}/{self.patience}"
            })

            # Decyzja o przerwaniu
            if no_improvement_count >= self.patience:
                self.reset_phermones(best_vehicles)
                # self.intensify_phermones()
                no_improvement_count = 0
                # print(Fore.RED + f"\n[EARLY STOPPING]" + Style.RESET_ALL + f" Brak poprawy przez {self.patience} iteracji. Przerywam w iteracji {i}.")
                # break

        self.problem.vehicles = best_vehicles

        history_data = {
            'overall': self.history_best_overall,
            'avg': self.history_avg_in_iter,
            'iter_best': self.history_best_in_iter
        }

        return best_vehicles, best_cost, history_data
