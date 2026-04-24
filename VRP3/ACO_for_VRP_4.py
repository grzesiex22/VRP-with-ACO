import numpy as np
from tqdm import tqdm
from colorama import Fore, Style, init

from VRP3.Ant_4 import Ant

from VRP3.Problem.VRP import VRP
from VRP3.Problem.Vehicle import Vehicle

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)


class ACO_for_VRP_4:

    def __init__(self, problem: VRP, ants=20, iterations=100, alpha=1, beta=2, evaporation=0.05,
                 patience=1000, patience_small_shake=200, patience_big_shake=500,
                 big_shake_evaporation=0.2, big_shake_duration=20,
                 intensity_small_shake=0.1, intensity_big_shake=0.3,
                 intensity_elite_ant=0.5, ranked_ants_count=(3, 10),
                 q_pheromone=10.0, tau_min=0.01, tau_max=5.0,
                 verbose=True):
        """
        Inicjalizuje algorytm optymalizacji mrówkowej (ACO) dla problemu VRP.

        Obiekty:
        ----------
        problem : VRP
            Obiekt przechowujący dane problemu (klienci, pojazdy itp.).


        Parametry klasycznego AC0
        ----------
        ants : int
            Liczba mrówek w kolonii generowana w każdej iteracji.
        iterations : int
            Maksymalna liczba iteracji algorytmu.
        alpha : float
            Wpływ śladu feromonowego. Wyższe wartości oznaczają większe podążanie za historią.
        beta : float
            Wpływ widoczności (heurystyki). Wyższe wartości to większa chęć odwiedzania bliższych celów.
        evaporation : float
            Współczynnik parowania feromonów (0.0 - 1.0). Wyższa wartość większe parowanie. Zapobiega przedwczesnej zbieżności.

        Parametry stagnacji
        ----------
        patience : int
            Maksymalna liczba iteracji bez poprawy globalnego rekordu przed przerwaniem algorytmu.
        patience_small_shake : int
            Liczba iteracji bez poprawy wyzwalająca lekkie przemieszanie feromonów (szum).
        patience_big_shake : int
            Liczba iteracji bez poprawy wyzwalająca głęboki reset feromonów i zmianę strategii.

        Parametry fazy wstrząsu
        ----------
        big_shake_evaporation : float
            Dodatkowe, mocniejsze parowanie feromonów w momencie wejścia w fazę Big Shake. Wyższa wartość większe parowanie.
        big_shake_duration : int
            Liczba iteracji trwania fazy Big Shake przed powrotem do normalnego trybu.
        intensity_small_shake : float
            Siła losowego szumu dodawanego do feromonów przy małym wstrząsie (np. 0.1 = 10%).
        intensity_big_shake : float
            Siła losowego szumu dodawanego do feromonów przy dużym wstrząsie (np. 0.1 = 10%).

        Parametry systemu rankingu elit
        ----------
        intensity_elite_ant : float
            Mnożnik wagi dla najlepszego rozwiązania wszech czasów (elity) przy aktualizacji feromonów.
        ranked_ants_count : tuple (int, int)
            Krotka (faza_normalna, faza_shake). Określa ile najlepszych mrówek z danej iteracji
            ma prawo zostawić feromony (np. 3 w normalnej fazie, 10 podczas wstrząsu dla większej eksploracji).

        Ograniczenia MMAS (MAX-MIN Ant System)
        ----------
        q_pheromone : float
            Stała wzmocnienia feromonu (ilość feromonu do podziału na trasę).
        tau_min : float
            Minimalny dozwolony poziom feromonów na krawędzi (zapobiega zerowaniu szans).
        tau_max : float
            Maksymalny dozwolony poziom feromonów na krawędzi (zapobiega dominacji jednej trasy).
        """

        self.verbose = verbose

        self.problem = problem
        self.ants = ants
        self.ranked_ants_count = ranked_ants_count

        self.iterations = iterations
        self.patience = patience
        self.patience_small_shake = patience_small_shake
        self.patience_big_shake = patience_big_shake

        self.big_shake_evaporation = big_shake_evaporation
        self.big_shake_duration = big_shake_duration
        self.intensity_big_shake = intensity_big_shake

        self.intensity_small_shake = intensity_small_shake
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
        self.history_small_shake = []  # epoki małych wstrząsów
        self.history_big_shake = []  # epoki dużych wstrząsów

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
            vehicle.duration = r_time_cost

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
            if self.verbose:
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

    def update_pheromone_rank(self, ants, best_gtr_overall, best_cost, ranked_ants_count=None):
        # 1. Parowanie (Evaporation)
        self.evaporate()

        # 2. Sortowanie mrówek od najlepszej (najniższy koszt)
        sorted_ants = sorted(ants, key=lambda x: x.cost)

        # 3. Parametr rankingu (np. top 6 mrówek zostawia ślad)
        for rank, ant in enumerate(sorted_ants[:ranked_ants_count]):
            ids = [node.id for node in ant.gtr]
            weight = ranked_ants_count - rank  # Najlepsza ma wagę 6, druga 5, itd.
            delta = (self.Q_pheromone / ant.cost) * weight

            for i in range(len(ids) - 1):
                a, b = ids[i], ids[i + 1]
                self.pheromone[a][b] += delta
                self.pheromone[b][a] += delta

        # 3. ELITIST UPDATE - Bonus dla mistrza
        # Najlepsza znaleziona trasa dostaje np. 5-krotnie silniejszy feromon
        if best_gtr_overall is not None:
            elite_weight = ranked_ants_count * self.intensity_elite_ant  # zwiększenie wagi dla elitarnego rozwiązania
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
        low = -intensity
        high = intensity
        noise = np.random.uniform(low, high, size=self.pheromone.shape)
        self.pheromone += noise * self.tau_max

        # 2. Wygładzanie (Pheromone Smoothing)
        # Przy dużym wzbudzeniu bardziej zbliżamy do tau_max, by wyrównać szanse
        smoothing_factor = intensity / 2
        self.pheromone = self.pheromone + smoothing_factor * (self.tau_max - self.pheromone)

        # 3. Pilnowanie granic MMAS
        self.pheromone = np.clip(self.pheromone, self.tau_min, self.tau_max)

    def calculate_diversity(self, ants_vehicles):
        """
        solutions: lista mrówek (self.ants)
        ant.vehicles: lista pojazdów
        vehicle.route: lista obiektów typu 'Road/Edge'
        road: obiekt posiadający węzły (np. road.from_node, road.to_node)
        """
        all_edge_sets = []

        for ant_vehicles in ants_vehicles:
            ant_edges = set()
            for ant_vehicle in ant_vehicles:
                # Iterujemy po liście dróg wewnątrz pojazdu
                route = ant_vehicle.route

                if not route or len(route) < 2:
                    continue

                # Przechodzimy po węzłach w trasie i tworzymy krawędzie
                for i in range(len(route) - 1):
                    u_id = route[i].id
                    v_id = route[i + 1].id

                    if u_id != v_id:
                        ant_edges.add(tuple((u_id, v_id)))

            if ant_edges:
                all_edge_sets.append(ant_edges)

        if not all_edge_sets:
            return 0.0

        # Całkowita liczba unikalnych krawędzi odkrytych przez całą populację
        U = len(set().union(*all_edge_sets))

        # Suma wszystkich krawędzi we wszystkich rozwiązaniach
        total_edges_sum = sum(len(s) for s in all_edge_sets)

        # Średnia liczba krawędzi na mrówkę
        avg_edges = total_edges_sum / len(all_edge_sets)

        # Mianownik normalizujący: różnica między totalną liczbą krawędzi a średnią
        denominator = total_edges_sum - avg_edges

        if denominator <= 0:
            return 0.0

        diversity = (U - avg_edges) / denominator

        return float(max(0.0, min(1.0, diversity)))

    def run(self):

        best_vehicles = None
        best_gtr_overall = None
        best_cost = float("inf")
        final_iter = 0
        best_iter_nr = 0

        no_improvement_count = 0
        no_improvement_count_shake = 0
        no_improvement_count_big_shake = 0
        is_big_shaking_phase = False
        big_shakes_counter = 0
        big_shakes_iters = []

        used_vehicles_count = 0
        vehicles_count = len(self.problem.vehicles)

        base_evaporation = self.evaporation
        base_beta = self.beta
        base_alpha = self.alpha

        # Tablice do przechowywania historii (do wykresu)
        self.history_best_overall = []  # Najlepszy koszt
        self.history_best_in_iter = []  # Najlepsze koszty każdej iteracji
        self.history_avg_in_iter = []  # Średni koszt w danej iteracj
        self.history_small_shake = []  # epoki małych wstrząsów
        self.history_big_shake = []  # epoki dużych wstrząsów

        # Tworzymy pasek postępu
        # Obsługa paska postępu zależnie od verbose
        iterator = range(self.iterations)
        if self.verbose:
            pbar = tqdm(iterator, desc="ACO 4", unit="it")
        else:
            pbar = iterator

        iter_vehicles = []

        # Pętla właściwa
        for i in pbar:
            ants = [Ant(self.problem) for _ in range(self.ants)]
            scores_matrix = (self.pheromone ** self.alpha) * self.eta_matrix
            # self.apply_depot_penalty(penalty_factor=0.5)  # Osłabienie feromonów powrotu do depot

            found_better_in_iter = False
            iter_costs = []
            iter_vehicles = []

            for ant in ants:
                ant.build_route(scores_matrix)

                cost, vehicles = self.solution_cost(ant.gtr)
                ant.cost = cost  # przyspieszenie

                iter_costs.append(cost)

                if cost < best_cost:
                    best_cost = cost
                    best_vehicles = vehicles
                    best_gtr_overall = ant.gtr.copy()  # (zapisujemy szkielet trasy)
                    best_iter_nr = i
                    used_vehicles_count = sum(1 for v in best_vehicles if len(v.route) > 2)
                    found_better_in_iter = True

                if no_improvement_count + 1 >= self.patience:
                    iter_vehicles.append(vehicles)

            # Aktualizacja feromonów
            if is_big_shaking_phase:
                # W fazie wstrząsu nie promujemy starego rekordu! Niech budują nowe ścieżki.
                # self.update_pheromone(ants)
                self.update_pheromone_rank(ants, best_gtr_overall, best_cost,
                                           ranked_ants_count=self.ranked_ants_count[1])
            else:
                # W fazie normalnej promujemy elitę
                self.update_pheromone_rank(ants, best_gtr_overall, best_cost,
                                           ranked_ants_count=self.ranked_ants_count[0])
                # self.update_pheromone_elite(ants, best_gtr_overall, best_cost)

            if not found_better_in_iter:
                no_improvement_count += 1
                no_improvement_count_shake += 1
                no_improvement_count_big_shake += 1
            else:
                no_improvement_count = 0
                no_improvement_count_shake = 0
                no_improvement_count_big_shake = 0

            # Pobudzenie feromonów - small shake
            if no_improvement_count_shake >= self.patience_small_shake and no_improvement_count < self.patience:
                self.shake_pheromones(intensity=self.intensity_small_shake)
                no_improvement_count_shake = 0
                self.history_small_shake.append(i)

            # Pobudzenie feromonów - big shake
            if no_improvement_count_big_shake >= self.patience_big_shake and no_improvement_count < self.patience:
                self.shake_pheromones(intensity=self.intensity_big_shake)
                is_big_shaking_phase = True
                big_shakes_counter += 1
                big_shakes_iters.append(i)
                no_improvement_count_shake = 0
                no_improvement_count_big_shake = 0
                self.history_big_shake.append(i)

                self.evaporation = min(self.evaporation * 1.3, 0.3)
                self.pheromone *= (1 - self.big_shake_evaporation)  # odparowanie przy big shake

                self.beta = 1.0
                self.alpha = 2.0  # może alfa większe podczas shake
                self.eta_matrix = (1.0 / (self.time_matrix_seconds + 1e-6)) ** self.beta

            # Zakończenie fazy big shake
            if is_big_shaking_phase and no_improvement_count_big_shake == self.big_shake_duration:
                # Po 30 iteracjach od wstrząsu, wracamy do trybu "dopracowywania trasy"
                is_big_shaking_phase = False
                self.evaporation = base_evaporation
                self.alpha = base_alpha
                self.beta = base_beta
                self.eta_matrix = (1.0 / (self.time_matrix_seconds + 1e-6)) ** self.beta

            # AKTUALIZACJA PASKA POSTĘPU
            if self.verbose:
                pbar.set_postfix({
                    "Best": f"{(best_cost/60):.2f} min",
                    "Veh": f"{used_vehicles_count}/{vehicles_count}",
                    "Evap": f"{self.evaporation:.2f}",
                    "Alfa": f"{self.alpha:.1f}",
                    "Beta": f"{self.beta:.1f}",
                    "Stagnation": f"{no_improvement_count}/{self.patience}",
                    "Small Shake": f"{no_improvement_count_shake}/{int(self.patience_small_shake)}",
                    "Big Shake": f"{no_improvement_count_big_shake}/{int(self.patience_big_shake)}"
                })

            # Zapisujemy historię
            self.history_best_overall.append(best_cost)
            self.history_avg_in_iter.append(sum(iter_costs) / len(iter_costs))
            self.history_best_in_iter.append(min(iter_costs))

            # Decyzja o przerwaniu
            if no_improvement_count >= self.patience:
                final_iter = i
                if self.verbose:
                    print(Fore.RED + f"\n[EARLY STOPPING]" + Style.RESET_ALL + f" Brak poprawy przez {self.patience} iteracji. Przerywam w iteracji {i}.")
                break

        self.problem.vehicles = best_vehicles

        diversity_final = self.calculate_diversity(ants_vehicles=iter_vehicles)

        history_data = {
            'overall': self.history_best_overall,
            'avg': self.history_avg_in_iter,
            'iter_best': self.history_best_in_iter,
            'small_shake': self.history_small_shake,
            'big_shake': self.history_big_shake,
            'iters_done': final_iter,
            'best_iter_nr': best_iter_nr,
            'big_shakes_iters': big_shakes_iters,
            'big_shakes_count': big_shakes_counter,
            'diversity_final': diversity_final
            }

        return best_vehicles, best_cost, history_data
