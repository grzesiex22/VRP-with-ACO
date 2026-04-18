from datetime import datetime, timedelta
from tqdm import tqdm
from datetime import timedelta
from colorama import Fore, Back, Style, init
import random
import math


from VRP3.Ant_3 import Ant
from VRP3.VRP import VRP
from VRP3.Vehicle import Vehicle

import sys

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)


class ACO_for_VRP_3:

    def __init__(self, problem: VRP, ants=50, iterations=100, alpha=1, beta=3, evaporation=0.03):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.phr_base_lvl = 0.3
        self.phr_min_lvl = 0.05
        self.phr_intensifier = 0.1
        self.pheromone = [[self.phr_base_lvl]*n for _ in range(n)]

        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation

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

    def update_pheromone(self, ants):
        # parowanie feromonu
        self.evaporate()

        # dodanie nowych feromonów
        for ant in ants:

            route = ant.gtr
            cost = ant.cost

            for i in range(len(route) - 1):
                a = route[i]
                b = route[i + 1]

                self.pheromone[a.id][b.id] += 1 / cost
                self.pheromone[b.id][a.id] += 1 / cost

    def update_best_iter(self, gtr):
        route = gtr
        cost, _ = self.solution_cost(route)

        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]

            self.pheromone[a.id][b.id] += 1 / cost
            self.pheromone[b.id][a.id] += 1 / cost

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


    def run(self, patience=100):
        best_vehicles = None
        best_cost = float("inf")
        no_improvement_count = 0

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
        pbar = tqdm(range(self.iterations), desc="ACO Optimization", unit="it")

        for i in pbar:

            ants = [Ant(self.problem) for _ in range(self.ants)]
            found_better_in_iter = False
            iter_costs = []

            for ant in ants:
                #### tu zrównoleglić
                ant.build_route(self.pheromone, self.alpha, self.beta)

                for i in range(5):
                    self.local_swap(ant.gtr)
                if random.random() < 0.3:
                    self.two_opt(ant.gtr, 10)

                cost, vehicles = self.solution_cost(ant.gtr)
                ant.cost = cost

                iter_costs.append(cost)

                # ELITSIM
                # best_iter_costs = [sys.maxsize]
                # # best iterations (ants) (elitsm)
                # for b_c in best_iter_costs:
                #     if cost in best_iter_costs:
                #         break
                #     if cost < b_c:
                #         best_iter_costs.append(b_c)
                #         best_iters.append(ant.gtr)
                #     if len(best_iter_costs) > num_best:
                #         maxi = max(best_iter_costs)
                #         idx = best_iter_costs.index(maxi)
                #         best_iters.pop(idx)
                #         best_iter_costs.pop(idx)

                # BEST IN ITERATION
                if cost < best_iter_cost:
                    best_iter_cost = cost
                    best_iter = ant.gtr

                # best globally
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

            self.evaporate()

            # elitism
            # for i in range(5):
            #     self.local_swap(best_iter)
            # if random.random() < 0.3:
            #     self.two_opt(best_iter, 10)

            self.update_best_iter(best_iter)


            # best_iter_cost = sys.maxsize
            # for gtr in best_iters:
            #     for i in range(5):
            #         self.local_swap(gtr)
            #     if random.random() < 0.1:
            #         self.two_opt(gtr, 10)
                
            #     cost = self.solution_cost(gtr)[0]
            #     if cost < best_iter_cost:
            #         best_iter_cost = cost
            #         best_iter = gtr

            # self.update_best_iter(best_iter)
            # best_iters = []

            # self.update_pheromone(best_iters)

            if not found_better_in_iter:
                no_improvement_count += 1

            # AKTUALIZACJA PASKA POSTĘPU
            pbar.set_postfix({
                "Best Cost": f"{(best_cost/60):.2f} min",
                "Stagnation": f"{no_improvement_count}/{patience}"
            })

            # Decyzja o przerwaniu
            if no_improvement_count >= patience:
                self.reset_phermones(best_vehicles)
                # self.intensify_phermones()
                no_improvement_count = 0
                # print(Fore.RED + f"\n[EARLY STOPPING]" + Style.RESET_ALL + f" Brak poprawy przez {patience} iteracji. Przerywam w iteracji {i}.")

        history_data = {
            'overall': self.history_best_overall,
            'avg': self.history_avg_in_iter,
            'iter_best': self.history_best_in_iter
        }

        return best_vehicles, best_cost, history_data