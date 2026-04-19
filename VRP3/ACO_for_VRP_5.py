from datetime import datetime, timedelta

import numpy as np
from tqdm import tqdm
from datetime import timedelta
from colorama import Fore, Back, Style, init

from VRP3.Ant_5 import Ant

from VRP3.VRP import VRP
from VRP3.Vehicle import Vehicle

from VRP3.Gready import greedy_vrp


# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)


class ACO_for_VRP_5:

    def __init__(self, problem: VRP, ants=20, iterations=100, alpha=1, beta=2, evaporation=0.05,
                 q_pheromone=1000.0, tau_min=0.01, tau_max=10.0):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.pheromone = np.ones((n, n))

        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation
        self.Q_pheromone = q_pheromone

        # ograniczenia feromonu
        self.tau_max = tau_max
        self.tau_min = tau_min

        # Konwertujemy listę list na macierz NumPy
        self.time_matrix_seconds = np.array(self.problem.time_matrix_seconds)

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
        time_matrix = self.time_matrix_seconds

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

    def update_pheromone(self, ants):
        # parowanie feromonu
        self.evaporate()

        # dodanie nowych feromonów
        for ant in ants:

            ids = [node.id for node in ant.gtr]
            d_tau = self.Q_pheromone / ant.cost

            for i in range(len(ids) - 1):
                a, b = ids[i], ids[i + 1]
                self.pheromone[a, b] += d_tau
                self.pheromone[b, a] += d_tau

        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def update_pheromone_elite(self, ants, best_gtr_overall, best_cost):
        # 1. Parowanie (Evaporation)
        self.evaporate()

        # 2. Aktualizacja od zwykłych mrówek
        for ant in ants:
            ids = [node.id for node in ant.gtr]
            d_tau = self.Q_pheromone / ant.cost

            for i in range(len(ids) - 1):
                a, b = ids[i], ids[i + 1]
                self.pheromone[a, b] += d_tau
                self.pheromone[b, a] += d_tau

        # 3. ELITIST UPDATE - Bonus dla mistrza
        # Najlepsza znaleziona trasa dostaje np. 5-krotnie silniejszy feromon
        if best_gtr_overall is not None:
            elite_weight = self.ants * 0.5  # Jakby 5 mrówek przeszło tą samą idealną trasą
            d_tau_elite = (self.Q_pheromone / best_cost) * elite_weight

            elite_ids = [node.id for node in best_gtr_overall]
            for i in range(len(elite_ids) - 1):
                a, b = elite_ids[i], elite_ids[i + 1]
                # Podwójne dodanie (graf nieskierowany)
                self.pheromone[a, b] += d_tau_elite
                self.pheromone[b, a] += d_tau_elite

        # 4. Limitowanie MAX/MIN (BEZ TEGO FEROMONY WYBUCHNĄ W KOSMOS)
        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def prepare_greeady_solution(self):
        # UWAGA: Zakładam, że masz funkcję run_greedy w VRP
        greedy_problem, greedy_cost = greedy_vrp(self.problem.nodes, self.problem.copy())

        # Traktujemy wynik Greedy jako najlepszy dotychczasowy
        print("Inicjalizacja gready - czas: " + Fore.YELLOW + f"{greedy_cost / 60} min")

        best_cost = greedy_cost
        best_vehicles = greedy_problem.vehicles

        # Składamy "surową" trasę GTR z pojazdów Greedy'ego, żeby dać jej feromony
        greedy_gtr = [self.problem.nodes[0]]  # Zaczynamy w bazie
        for v in best_vehicles:
            # Dodajemy klientów z trasy pojazdu (pomijamy zera na początku/końcu, jeśli są dublowane)
            for node in v.route:
                if node.id != 0 or greedy_gtr[-1].id != 0:
                    greedy_gtr.append(node)

        best_gtr_overall = greedy_gtr

        # Dajemy gigantyczny zastrzyk feromonu na trasę Greedy na start!
        self.update_pheromone_elite([], best_gtr_overall, best_cost)

        return best_vehicles, best_gtr_overall, best_cost

    def run(self, patience=100):
        best_vehicles, best_gtr_overall, best_cost = self.prepare_greeady_solution()

        no_improvement_count = 0

        # Tablice do przechowywania historii (do wykresu)
        self.history_best_overall = []  # Najlepszy koszt
        self.history_best_in_iter = []  # Najlepsze koszty każdej iteracji
        self.history_avg_in_iter = []  # Średni koszt w danej iteracj

        # Tworzymy pasek postępu
        pbar = tqdm(range(self.iterations), desc="ACO Optimization", unit="it")

        for i in pbar:

            ants = [Ant(self.problem) for _ in range(self.ants)]
            scores_matrix = (self.pheromone ** self.alpha) * self.eta_matrix

            found_better_in_iter = False
            iter_costs = []

            for ant in ants:

                #### tu zrównoleglić

                ant.build_route(scores_matrix)

                cost, vehicles = self.solution_cost(ant.gtr)
                ant.cost = cost  # przyspieszenie
                iter_costs.append(cost)

                if cost < best_cost:
                    best_cost = cost
                    best_vehicles = vehicles
                    best_gtr_overall = ant.gtr.copy()  # (zapisujemy szkielet trasy)
                    no_improvement_count = 0
                    found_better_in_iter = True
                #### tu zrównoleglić - koniec

                # można podbijać losowo feromony gdy stagnacja

            # Zapisujemy historię
            self.history_best_overall.append(best_cost)
            self.history_avg_in_iter.append(sum(iter_costs) / len(iter_costs))
            self.history_best_in_iter.append(min(iter_costs))

            # self.update_pheromone(ants)
            self.update_pheromone_elite(ants, best_gtr_overall, best_cost)

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

        self.problem.vehicles = best_vehicles

        history_data = {
            'overall': self.history_best_overall,
            'avg': self.history_avg_in_iter,
            'iter_best': self.history_best_in_iter
        }

        return best_vehicles, best_cost, history_data
