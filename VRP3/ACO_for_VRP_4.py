from datetime import datetime, timedelta

import numpy as np
from tqdm import tqdm
from datetime import timedelta
from colorama import Fore, Back, Style, init

from VRP3.Ant_4 import Ant

from VRP3.VRP import VRP
from VRP3.Vehicle import Vehicle

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)


class ACO_for_VRP_4:

    def __init__(self, problem: VRP, ants=20, iterations=100, alpha=1, beta=2, evaporation=0.05,
                 patience=1000, patience_small_shake=200, patience_big_shake=500,
                 intensity_small_shake=0.1, intensity_big_shake=0.3, intensity_elite_ant=0.5,
                 q_pheromone=10.0, tau_min=0.01, tau_max=5.0):

        self.problem = problem
        self.ants = ants

        self.iterations = iterations
        self.patience = patience
        self.patience_small_shake = patience_small_shake
        self.patience_big_shake = patience_big_shake

        self.intensity_small_shake = intensity_small_shake
        self.intensity_big_shake = intensity_big_shake
        self.intensity_elite_ant = intensity_elite_ant

        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation

        # ograniczenia feromonu
        self.Q_pheromone = q_pheromone  # wzmocnienie feromonu
        self.tau_max = tau_max  # ograniczenie od góry
        self.tau_min = tau_min  # ograniczenie od dołu

        n = len(problem.nodes)
        self.pheromone = np.ones((n, n))

        # Konwertujemy listę list na macierz NumPy
        self.time_matrix_seconds = np.array(self.problem.time_matrix_seconds)

        # do szybszego odczytu potęg
        self.eta_matrix = (1.0 / (self.time_matrix_seconds + 1e-6)) ** self.beta

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
            current_time_s += time_matrix[a.id, b.id]

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
            elite_weight = self.ants * self.intensity_elite_ant  # Jakby 5 mrówek przeszło tą samą idealną trasą
            d_tau_elite = (self.Q_pheromone / best_cost) * elite_weight

            elite_ids = [node.id for node in best_gtr_overall]
            for i in range(len(elite_ids) - 1):
                a, b = elite_ids[i], elite_ids[i + 1]
                # Podwójne dodanie (graf nieskierowany)
                self.pheromone[a, b] += d_tau_elite
                self.pheromone[b, a] += d_tau_elite

        # 4. Limitowanie MAX/MIN (BEZ TEGO FEROMONY WYBUCHNĄ W KOSMOS)
        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def update_pheromone_rank(self, ants, best_gtr_overall, best_cost):
        # 1. Parowanie (Evaporation)
        self.evaporate()

        # 2. Sortowanie mrówek od najlepszej (najniższy koszt)
        sorted_ants = sorted(ants, key=lambda x: x.cost)

        # 3. Parametr rankingu (np. top 6 mrówek zostawia ślad)
        w = 10
        for rank, ant in enumerate(sorted_ants[:w]):
            ids = [node.id for node in ant.gtr]
            weight = w - rank  # Najlepsza ma wagę 6, druga 5, itd.
            delta = weight / ant.cost
            for i in range(len(ids) - 1):
                a, b = ids[i], ids[i + 1]
                self.pheromone[a][b] += delta
                self.pheromone[b][a] += delta

        # 3. ELITIST UPDATE - Bonus dla mistrza
        # Najlepsza znaleziona trasa dostaje np. 5-krotnie silniejszy feromon
        if best_gtr_overall is not None:
            elite_weight = self.ants * self.intensity_elite_ant  # Jakby 5 mrówek przeszło tą samą idealną trasą
            d_tau_elite = (self.Q_pheromone / best_cost) * elite_weight

            elite_ids = [node.id for node in best_gtr_overall]
            for i in range(len(elite_ids) - 1):
                a, b = elite_ids[i], elite_ids[i + 1]
                # Podwójne dodanie (graf nieskierowany)
                self.pheromone[a, b] += d_tau_elite
                self.pheromone[b, a] += d_tau_elite

        # 4. Limitowanie MAX/MIN (BEZ TEGO FEROMONY WYBUCHNĄ W KOSMOS)
        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def shake_pheromones(self, intensity=0.2):
        """
        intensity: jak mocno potrząsamy (0.1 = 10%, 0.4 = 40%)
        """
        # 1. Dodanie losowego szumu na podstawie intensywności
        low = 1.0 - intensity
        high = 1.0 + intensity
        noise = np.random.uniform(low, high, size=self.pheromone.shape)
        self.pheromone *= noise

        # 2. Wygładzanie (Pheromone Smoothing)
        # Przy dużym wzbudzeniu bardziej zbliżamy do tau_max, by wyrównać szanse
        smoothing_factor = intensity / 2
        self.pheromone = self.pheromone + smoothing_factor * (self.tau_max - self.pheromone)

        # 3. Pilnowanie granic MMAS
        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def run(self):

        best_vehicles = None
        best_gtr_overall = None
        best_cost = float("inf")

        no_improvement_count = 0
        no_improvement_count_shake = 0
        no_improvement_count_big_shake = 0

        base_evaporation = self.evaporation
        base_beta = self.beta
        base_alpha = self.alpha

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
                ant.build_route(scores_matrix)

                cost, vehicles = self.solution_cost(ant.gtr)
                ant.cost = cost  # przyspieszenie

                iter_costs.append(cost)

                if cost < best_cost:
                    best_cost = cost
                    best_vehicles = vehicles
                    best_gtr_overall = ant.gtr.copy()  # (zapisujemy szkielet trasy)
                    found_better_in_iter = True

            # Zapisujemy historię
            self.history_best_overall.append(best_cost)
            self.history_avg_in_iter.append(sum(iter_costs) / len(iter_costs))
            self.history_best_in_iter.append(min(iter_costs))

            # Aktualizacja feromonów
            # self.update_pheromone(ants)
            # self.update_pheromone_elite(ants, best_gtr_overall, best_cost)
            # self.update_pheromone_rank(ants, best_gtr_overall, best_cost)

            is_shaking_phase = (0 < no_improvement_count_big_shake < 30)

            if is_shaking_phase:
                # W fazie wstrząsu nie promujemy starego rekordu! Niech budują nowe ścieżki.
                self.update_pheromone(ants)
            else:
                # W fazie normalnej promujemy elitę
                self.update_pheromone_rank(ants, best_gtr_overall, best_cost)

            if not found_better_in_iter:
                no_improvement_count += 1
                no_improvement_count_shake += 1
                no_improvement_count_big_shake += 1
            else:
                no_improvement_count = 0
                no_improvement_count_shake = 0
                no_improvement_count_big_shake = 0

                self.evaporation = base_evaporation
                self.alpha = base_alpha
                self.beta = base_beta
                self.eta_matrix = (1.0 / (self.time_matrix_seconds + 1e-6)) ** self.beta

            # Pobudzenie feromonów small
            if no_improvement_count_shake >= self.patience_small_shake:
                self.shake_pheromones(intensity=self.intensity_small_shake)
                no_improvement_count_shake = 0

                self.evaporation = min(self.evaporation * 1.1, 0.3)

            # Pobudzenie feromonów big
            if no_improvement_count_big_shake >= self.patience_big_shake:
                self.shake_pheromones(intensity=self.intensity_big_shake)
                no_improvement_count_big_shake = 0

                self.evaporation = min(self.evaporation * 1.3, 0.3)
                self.pheromone *= (1 - self.evaporation * 0.5)

                self.beta = min(self.beta * 1.5, 8)
                self.alpha = max(self.alpha * 0.8, 0.5)
                self.eta_matrix = (1.0 / (self.time_matrix_seconds + 1e-6)) ** self.beta

            if no_improvement_count_big_shake == 30 or no_improvement_count_shake == 20:
                # Po 15 iteracjach od wstrząsu, wracamy do trybu "dopracowywania trasy"
                self.evaporation = base_evaporation
                self.alpha = base_alpha
                self.beta = base_beta
                self.eta_matrix = (1.0 / (self.time_matrix_seconds + 1e-6)) ** self.beta
                # (Opcjonalnie) wypisz printa, żebyś widział na konsoli, że chłodzenie działa

            # AKTUALIZACJA PASKA POSTĘPU
            pbar.set_postfix({
                "Best Cost": f"{(best_cost/60):.2f} min",
                "Alfa": f"{self.alpha:.1f}",
                "Beta": f"{self.beta:.1f}",
                "Stagnation": f"{no_improvement_count}/{self.patience}",
                "Small Shake": f"{no_improvement_count_shake}/{int(self.patience_small_shake)}",
                "Big Shake": f"{no_improvement_count_big_shake}/{int(self.patience_big_shake)}"
            })

            # Decyzja o przerwaniu
            if no_improvement_count >= self.patience:
                print(Fore.RED + f"\n[EARLY STOPPING]" + Style.RESET_ALL + f" Brak poprawy przez {self.patience} iteracji. Przerywam w iteracji {i}.")
                break

        self.problem.vehicles = best_vehicles

        history_data = {
            'overall': self.history_best_overall,
            'avg': self.history_avg_in_iter,
            'iter_best': self.history_best_in_iter
        }

        return best_vehicles, best_cost, history_data
