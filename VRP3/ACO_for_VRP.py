from datetime import datetime, timedelta
from tqdm import tqdm

from VRP3.Ant import Ant
from VRP3.VRP import VRP
from VRP3.Vehicle import Vehicle


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
                overload = vehicle.filling - vehicle.capacity
                capacity_penalty = overload * 10000  # Bardzo ciężka kara

            # total_time = max(self.route_cost(route), total_time)
            total_time += (r_time_cost + capacity_penalty)

            # C. Kolekcjonujemy ID klientów (do sprawdzenia czy wszyscy obsłużeni)
            for n in vehicle.route:
                if n.id != 0:
                    all_visited_ids.add(n.id)

        # 3. Kara za nieodwiedzenie wszystkich (Safety net)
        num_clients = len(self.problem.nodes) - 1
        if len(all_visited_ids) < num_clients:
            total_time += (num_clients - len(all_visited_ids)) * 100000

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
                print(f"\n[EARLY STOPPING] Brak poprawy przez {patience} iteracji. Przerywam w iteracji {i}.")
                break

        return best_vehicles, best_cost

    def print_summary(self, vehicles):
        """Wyświetla szczegółowy harmonogram, pojemności i podsumowanie czasowe."""
        print("\n" + "=" * 115)  # Rozszerzona linia dla nowych kolumn
        print(f"{'PODSUMOWANIE TRAS I HARMONOGRAM':^115}")
        print("=" * 115)

        time_matrix = self.problem.time_matrix_seconds
        grand_total_seconds = 0.0

        for vehicle in vehicles:
            route = vehicle.route
            if len(route) <= 2:
                continue

            print(f"\n[ POJAZD ID: {vehicle.id:2d} | Pojemność Max: {vehicle.capacity} "
                  f"| Pojemność użyta: {vehicle.filling} | Ilość klientów: {len(vehicle.route)-2} ]")
            # Nagłówek z nowymi kolumnami: Pop (Popyt punktu) | Auto (Ładunek w aucie)
            print(
                f"{'Punkt':<12} | {'Pop':<5} | {'Auto':<6} | {'Okno czasowe':<15} | {'Przyjazd':<10} | {'Start serwisu':<15} | {'Odjazd':<10} | {'Info'}")
            print("-" * 115)

            current_time_s = 0.0
            current_load = 0

            for i in range(len(route)):
                node = route[i]

                # Aktualizacja ładunku (popyt punktu)
                current_load += node.demand

                if i == 0:
                    # Start z bazy
                    print(
                        f"START Baza   | {node.demand:<5} | {current_load:<6} | {'-':<15} | {'-':<10} | {'00:00:00':<15} | 00:00:00   | Wyjazd")
                    continue

                # 1. Dojazd
                travel_time = time_matrix[route[i - 1].id][node.id]
                arrival_time_s = current_time_s + travel_time

                # 2. Logika okien czasowych
                wait_time_s = 0.0
                penalty_s = 0.0
                status_msg = ""

                if node.id != 0:
                    if arrival_time_s < node.time_window_s[0]:
                        wait_time_s = node.time_window_s[0] - arrival_time_s
                        status_msg = f"Czekanie: {wait_time_s / 60:.1f} min"
                    elif arrival_time_s > node.time_window_s[1]:
                        penalty_s = node.penalty_s[1]
                        status_msg = f"KARA: {penalty_s / 60:.1f} min"

                # 3. Rozpoczęcie obsługi i odjazd
                start_service_s = arrival_time_s + wait_time_s + penalty_s

                if node.id == 0:  # Powrót do bazy
                    departure_time_s = arrival_time_s
                    label = "KONIEC Baza"
                else:
                    departure_time_s = start_service_s + node.service_s
                    label = f"Klient {node.id}"

                # Formatowanie
                arr_str = str(timedelta(seconds=int(arrival_time_s)))
                start_str = str(timedelta(seconds=int(start_service_s)))
                dep_str = str(timedelta(seconds=int(departure_time_s)))
                tw_str = f"{node.time_window[0].strftime('%H:%M')}-{node.time_window[1].strftime('%H:%M')}"

                # Wyświetlanie wiersza z uwzględnieniem Pop i Auto
                print(
                    f"{label:<12} | {node.demand:<5} | {current_load:<6} | {tw_str:<15} | {arr_str:<10} | {start_str:<15} | {dep_str:<10} | {status_msg}")

                current_time_s = departure_time_s

            vehicle_total_min = current_time_s / 60
            grand_total_seconds += current_time_s
            print(f"--- Czas trasy pojazdu {vehicle.id}: {vehicle_total_min:.2f} min ({current_time_s:.0f} sek) ---")

        print("\n" + "=" * 115)
        print(f"{'ŁĄCZNY KOSZT WSZYSTKICH TRAS: ' + f'{grand_total_seconds / 60:.2f}' + ' MINUT':^115}")
        print(f"{'ŁĄCZNY KOSZT W SEKUNDACH: ' + f'{grand_total_seconds:.0f}' + ' s':^115}")
        print("=" * 115)