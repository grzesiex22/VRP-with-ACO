from datetime import datetime, timedelta

from VRP2.Ant import Ant
from VRP2.VRP import VRP


class ACO_for_VRP:

    def __init__(self, problem: VRP, ants=20, iterations=100):

        self.problem = problem
        self.ants = ants
        self.iterations = iterations

        n = len(problem.nodes)
        self.pheromone = [[1]*n for _ in range(n)]

        self.alpha = 1
        self.beta = 2
        self.evaporation = 0.5

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

    def solution_cost(self, routes):

        total_time = 0.0

        for route in routes:
            # total_time = max(self.route_cost(route), total_time)
            total_time += self.route_cost(route)

        return total_time

    def evaporate(self):

        n = len(self.pheromone)

        for i in range(n):
            for j in range(n):
                self.pheromone[i][j] *= (1 - self.evaporation)

    def update_pheromone(self, ants):

        n = len(self.pheromone)

        # parowanie feromonu
        for i in range(n):
            for j in range(n):
                self.pheromone[i][j] *= (1 - self.evaporation)

        # dodanie nowych feromonów
        for ant in ants:

            routes = [v.routes for v in ant.vehicles]
            for route in routes:
                cost = self.route_cost(route)

                for i in range(len(route) - 1):
                    a = route[i]
                    b = route[i + 1]

                    self.pheromone[a.id][b.id] += 1 / cost
                    self.pheromone[b.id][a.id] += 1 / cost

    def run(self):

        best_vehicles = None
        best_cost = float("inf")

        for i in range(self.iterations):

            # if i % 10 == 0:
            #     print(f"{i}")

            ants = [Ant(self.problem) for _ in range(self.ants)]

            for ant in ants:

                ant.build_route(self.pheromone, self.alpha, self.beta)

                cost = self.solution_cost([v.routes for v in ant.vehicles])

                if cost < best_cost:
                    best_cost = cost
                    best_vehicles = ant.vehicles

            self.update_pheromone(ants)

        return best_vehicles, best_cost

    def print_summary(self, vehicles):
        """Wyświetla szczegółowy harmonogram i podsumowanie czasowe w minutach."""
        print("\n" + "=" * 80)
        print(f"{'PODSUMOWANIE TRAS I HARMONOGRAM':^80}")
        print("=" * 80)

        time_matrix = self.problem.time_matrix_seconds
        grand_total_seconds = 0.0

        for vehicle in vehicles:
            route = vehicle.routes
            if len(route) <= 2:  # Pomiń puste trasy (tylko baza-baza)
                continue

            print(f"\n[ POJAZD ID: {vehicle.id:2d} | Pojemność: {vehicle.filling}/{vehicle.capacity} ]")
            print(
                f"{'Punkt':<12} | {'Okno czasowe':<15} | {'Przyjazd':<10} | {'Start serwisu':<15} | {'Odjazd':<10} | {'Info'}")
            print("-" * 95)

            current_time_s = 0.0
            route_start_time = 0.0

            for i in range(len(route)):
                node = route[i]

                if i == 0:
                    # Start z bazy
                    print(f"START Baza   | {'-':<15} | {'-':<10} | {'00:00:00':<15} | 00:00:00   | Wyjazd")
                    continue

                # 1. Dojazd
                travel_time = time_matrix[route[i - 1].id][node.id]
                arrival_time_s = current_time_s + travel_time

                # 2. Logika okien czasowych (tylko dla klientów)
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

                # Konwersja na format czytelny
                arr_str = str(timedelta(seconds=int(arrival_time_s)))
                start_str = str(timedelta(seconds=int(start_service_s)))
                dep_str = str(timedelta(seconds=int(departure_time_s)))
                tw_str = f"{node.time_window[0].strftime('%H:%M')}-{node.time_window[1].strftime('%H:%M')}"

                print(f"{label:<12} | {tw_str:<15} | {arr_str:<10} | {start_str:<15} | {dep_str:<10} | {status_msg}")

                current_time_s = departure_time_s

            # Podsumowanie dla pojedynczego pojazdu
            vehicle_total_min = current_time_s / 60
            grand_total_seconds += current_time_s
            print(f"--- Czas trasy pojazdu {vehicle.id}: {vehicle_total_min:.2f} min ({current_time_s:.0f} sek) ---")

        print("\n" + "=" * 80)
        print(f"ŁĄCZNY KOSZT WSZYSTKICH TRAS: {grand_total_seconds / 60:.2f} MINUT")
        print(f"ŁĄCZNY KOSZT W SEKUNDACH:     {grand_total_seconds:.0f} s")
        print("=" * 80)