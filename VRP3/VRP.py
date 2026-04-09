import math
from datetime import timedelta
from colorama import Fore, Back, Style, init

from VRP3.Node import Node
from VRP3.Vehicle import Vehicle

# Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
init(autoreset=True)

class VRP:

    def __init__(self, nodes: [Node], vehicles: [Vehicle], depot_index=0):
        self.nodes = nodes
        self.vehicles = vehicles
        self.depot = nodes[depot_index]
        self.time_matrix = self.time_matrix()
        self.time_matrix_seconds = self.time_matrix_seconds()

    def distance(self, a, b):
        return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

    def time(self, a, b, velocity=60):
        # Tworzymy obiekt przedziału czasowego
        return timedelta(hours=self.distance(a, b) / velocity)

    def time_matrix(self):

        n = len(self.nodes)
        matrix = [[timedelta(0)] * n for _ in range(n)]

        for i in range(n):
            for j in range(n):
                matrix[i][j] = self.time(self.nodes[i], self.nodes[j])

        return matrix

    def time_matrix_seconds(self):
        n = len(self.nodes)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):  # Optymalizacja: liczymy tylko połowę macierzy

                duration = self.time(self.nodes[i], self.nodes[j])
                seconds = duration.total_seconds()

                # Wpisujemy do macierzy (symetrycznie)
                matrix[i][j] = seconds
                matrix[j][i] = seconds

        return matrix

    def print_summary(self, vehicles):
        """Wyświetla kolorowy, wyrównany harmonogram i statystyki końcowe."""
        # Nagłówek główny
        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 118)
        print(f"{'PODSUMOWANIE TRAS I HARMONOGRAM':^118}")
        print("-" * 118 + Style.RESET_ALL)

        time_matrix = self.time_matrix_seconds
        grand_total_seconds = 0.0
        total_clients_in_problem = len(self.nodes) - 1
        visited_client_ids = set()

        # Lista do śledzenia przeładowanych pojazdów
        overloaded_vehicles = []

        for vehicle in vehicles:
            route = vehicle.route
            if len(route) <= 2:
                continue

            # Sprawdzanie przeładowania dla statystyk końcowych
            if vehicle.filling > vehicle.capacity:
                overloaded_vehicles.append(str(vehicle.id))

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

        # 1. Status odwiedzin

        if num_visited == total_clients_in_problem:
            visit_color = Fore.GREEN
            all_clients_visited = True
        else:
            visit_color = Fore.RED
            all_clients_visited = False

        print(
            f"  Odwiedzeni klienci: {visit_color}{num_visited} / {total_clients_in_problem} ({(num_visited / total_clients_in_problem) * 100:.1f}%){Style.RESET_ALL}")

        # 2. Status pojemności floty
        if not overloaded_vehicles:
            print(f"  Pojemność floty:    {Fore.GREEN}OK - wszystkie pojazdy w normie{Style.RESET_ALL}")
        else:
            ids_str = ", ".join(overloaded_vehicles)
            print(
                f"  Pojemność floty:    {Fore.RED}{Style.BRIGHT}PRZEKROCZONA w pojazdach ID: {ids_str}{Style.RESET_ALL}")

        # 3. Ostrzeżenie o brakach
        if num_visited < total_clients_in_problem:
            missing = total_clients_in_problem - num_visited
            print(
                f"{Back.RED}{Fore.WHITE}{Style.BRIGHT}  UWAGA: NIE ODWIEDZONO WSZYSTKICH! BRAKUJE: {missing} KLIENTÓW!  {Style.RESET_ALL}")

        print(f"  Łączny koszt czasowy floty: {Fore.YELLOW}{grand_total_seconds / 60:.2f} min{Style.RESET_ALL}")
        print(f"  Użyte pojazdy: {len([v for v in vehicles if len(v.route) > 2])} / {len(vehicles)}")
        print(Fore.CYAN + "=" * 118 + Style.RESET_ALL)

        return all_clients_visited and not overloaded_vehicles
