from datetime import datetime, timedelta
from tqdm import tqdm
from datetime import timedelta
from colorama import Fore, Back, Style, init


from VRP3.Ant import Ant
from VRP3.VRP import VRP
from VRP3.Vehicle import Vehicle

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)

class ACO_for_VRP:

    def __init__(self, problem: VRP, ants=20, iterations=100, alpha=1, beta=2, evaporation=0.05):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.pheromone = [[1]*n for _ in range(n)]

        self.alpha = alpha
        self.beta = beta
        self.evaporation = evaporation

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
                capacity_penalty = overload * 100  # Bardzo ciężka kara

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
            cost, _ = self.solution_cost(route)

            for i in range(len(route) - 1):
                a = route[i]
                b = route[i + 1]

                self.pheromone[a.id][b.id] += 1 / cost
                self.pheromone[b.id][a.id] += 1 / cost

    def run(self, patience=100):

        best_vehicles = None
        best_cost = float("inf")
        no_improvement_count = 0

        # Tworzymy pasek postępu
        pbar = tqdm(range(self.iterations), desc="ACO Optimization", unit="it")

        for i in pbar:

            ants = [Ant(self.problem) for _ in range(self.ants)]
            found_better_in_iter = False

            for ant in ants:

                #### tu zrównoleglić
                ant.build_route(self.pheromone, self.alpha, self.beta)

                cost, vehicles = self.solution_cost(ant.gtr)

                if cost < best_cost:
                    best_cost = cost
                    best_vehicles = vehicles
                    no_improvement_count = 0
                    found_better_in_iter = True
                #### tu zrównoleglić - koniec

                # early stoping
                # można podbijać losowo feromony gdy stagnacja

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

        return best_vehicles, best_cost

    def print_summary(self, vehicles):
        """Wyświetla kolorowy, wyrównany harmonogram i statystyki końcowe."""
        # Nagłówek główny
        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 118)
        print(f"{'PODSUMOWANIE TRAS I HARMONOGRAM':^118}")
        print("-" * 118 + Style.RESET_ALL)

        time_matrix = self.problem.time_matrix_seconds
        grand_total_seconds = 0.0
        total_clients_in_problem = len(self.problem.nodes) - 1
        visited_client_ids = set()

        for vehicle in vehicles:
            route = vehicle.route
            if len(route) <= 2:
                continue

            # Kolorowanie nagłówka pojazdu (Zielony = OK, Czerwony = Przeładowany)
            load_color = Fore.GREEN if vehicle.filling <= vehicle.capacity else Fore.RED

            print(f"\n{Fore.YELLOW}# POJAZD ID: {vehicle.id:2d}{Style.RESET_ALL} | "
                  f"Pojemność: {load_color}{vehicle.filling}/{vehicle.capacity}{Style.RESET_ALL} | "
                  f"Klienci: {len(vehicle.route) - 2}")

            # Nagłówek tabeli
            print(
                f"{Style.DIM}{'Punkt':<12} | {'Pop':<5} | {'Auto':<6} | {'Okno czasowe':<15} | {'Przyjazd':<10} | {'Start serwisu':<15} | {'Odjazd':<10} | {'Info'}{Style.RESET_ALL}")
            print("-" * 118)

            current_time_s = 0.0
            current_load = 0

            for i in range(len(route)):
                node = route[i]
                current_load += node.demand

                if node.id != 0:
                    visited_client_ids.add(node.id)

                # --- LOGIKA CZASOWA ---
                wait_time_s = 0.0
                penalty_s = 0.0
                status_msg = ""

                if i == 0:
                    # Start z bazy
                    arrival_time_s = 0.0
                    start_service_s = 0.0
                    departure_time_s = 0.0
                    label = f"{Fore.BLUE}START Baza  {Fore.RESET}"
                    tw_str = "-"
                    status_msg = "Wyjazd"
                else:
                    # Dojazd do klienta lub powrót do bazy
                    travel_time = time_matrix[route[i - 1].id][node.id]
                    arrival_time_s = current_time_s + travel_time

                    if node.id != 0:
                        # Sprawdzanie okien czasowych tylko dla klientów
                        if arrival_time_s < node.time_window_s[0]:
                            wait_time_s = node.time_window_s[0] - arrival_time_s
                            status_msg = f"{Fore.CYAN}Czekanie: {wait_time_s / 60:.1f} min{Fore.RESET}"
                        elif arrival_time_s > node.time_window_s[1]:
                            penalty_s = node.penalty_s[1]
                            status_msg = f"{Fore.RED}{Style.BRIGHT}KARA: {penalty_s / 60:.1f} min{Style.RESET_ALL}"

                        start_service_s = arrival_time_s + wait_time_s + penalty_s
                        departure_time_s = start_service_s + node.service_s
                        label = f"Klient {node.id:<4}"
                        tw_str = f"{node.time_window[0].strftime('%H:%M')}-{node.time_window[1].strftime('%H:%M')}"
                    else:
                        # Powrót do bazy (id=0)
                        start_service_s = arrival_time_s
                        departure_time_s = arrival_time_s
                        label = f"{Fore.BLUE}KONIEC Baza {Fore.RESET}"
                        tw_str = f"{node.time_window[0].strftime('%H:%M')}-{node.time_window[1].strftime('%H:%M')}"

                # --- FORMATOWANIE STRINGÓW ---
                arr_str = str(timedelta(seconds=int(arrival_time_s))) if i > 0 else "-"
                start_str = str(timedelta(seconds=int(start_service_s)))
                dep_str = str(timedelta(seconds=int(departure_time_s)))

                # WYŚWIETLANIE WIERSZA (Szerokość punktu 21 wyrównuje kolumny z kolorami ANSI)
                print(
                    f"{label:<12} | "
                    f"{node.demand:<5} | "
                    f"{current_load:<6} | "
                    f"{tw_str:<15} | "
                    f"{arr_str:<10} | "
                    f"{start_str:<15} | "
                    f"{dep_str:<10} | "
                    f"{status_msg}"
                )

                current_time_s = departure_time_s

            grand_total_seconds += current_time_s
            print(f"{Style.DIM}--- Czas trasy: {current_time_s / 60:.2f} min ---{Style.RESET_ALL}")

        # --- STOPKA ZBIORCZA ---
        num_visited = len(visited_client_ids)
        print("\n" + Fore.CYAN + "=" * 118)
        print(f"{'STATYSTYKI KOŃCOWE':^118}")
        print("-" * 118 + Style.RESET_ALL)

        visit_color = Fore.GREEN if num_visited == total_clients_in_problem else Fore.RED
        print(
            f"  Odwiedzeni klienci: {visit_color}{num_visited} / {total_clients_in_problem} ({(num_visited / total_clients_in_problem) * 100:.1f}%){Style.RESET_ALL}")

        if num_visited < total_clients_in_problem:
            missing = total_clients_in_problem - num_visited
            print(
                f"{Fore.WHITE}{Style.BRIGHT}  UWAGA: NIE ODWIEDZONO WSZYSTKICH! BRAKUJE: {missing} KLIENTÓW!  {Style.RESET_ALL}")

        print(f"  Łączny koszt czasowy floty: {Fore.YELLOW}{grand_total_seconds / 60:.2f} min{Style.RESET_ALL}")
        print(f"  Użyte pojazdy: {len([v for v in vehicles if len(v.route) > 2])} / {len(vehicles)}")
        print(Fore.CYAN + "=" * 118 + Style.RESET_ALL)