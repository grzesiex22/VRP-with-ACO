from datetime import timedelta

import numpy as np
from colorama import Fore, Back, Style, init
from VRP3.Problem.VRP import VRP
# Inicjalizacja colorama (dla pewności, jeśli nie była wywołana wcześniej)
init(autoreset=True)


class Summarizer:
    def __init__(self, problem: VRP):
        """
        :param problem: Obiekt klasy VRP zawierający macierz czasu i listę węzłów.
        """
        self.problem = problem

    def generate_summary(self, pheromone=None):
        """
            Wyświetla harmonogram oraz statystyki.
            pheromone: opcjonalna macierz (numpy array lub lista list).
        """

        print("\n" + Fore.CYAN + Style.BRIGHT + "=" * 118)
        print(f"{'PODSUMOWANIE TRAS I HARMONOGRAM':^118}")
        print("-" * 118 + Style.RESET_ALL)

        time_matrix = self.problem.time_matrix_seconds
        grand_total_seconds = 0.0
        total_clients_in_problem = len(self.problem.nodes) - 1
        visited_client_ids = set()
        overloaded_vehicles = []

        for vehicle in self.problem.vehicles:
            route = vehicle.route
            if len(route) <= 2:
                continue

            if vehicle.filling > vehicle.capacity:
                overloaded_vehicles.append(str(vehicle.id))

            load_color = Fore.GREEN if vehicle.filling <= vehicle.capacity else Fore.RED

            print(f"\n{Fore.YELLOW}# POJAZD ID: {vehicle.id:2d}{Style.RESET_ALL} | "
                  f"Pojemność: {load_color}{vehicle.filling}/{vehicle.capacity}{Style.RESET_ALL} | "
                  f"Klienci: {len(vehicle.route) - 2}")

            print(f"{Style.DIM}{'Punkt':<12} | {'Pop':<5} | {'Auto':<6} | {'Okno czasowe':<15} | "
                  f"{'Przyjazd':<10} | {'Start serwisu':<15} | {'Odjazd':<10} | {'Info'}{Style.RESET_ALL}")
            print("-" * 118)

            current_time_s = 0.0
            current_load = 0

            for i in range(len(route)):
                node = route[i]
                current_load += node.demand

                if node.id != 0:
                    visited_client_ids.add(node.id)

                wait_time_s = 0.0
                penalty_s = 0.0
                status_msg = ""

                if i == 0:
                    arrival_time_s = 0.0
                    start_service_s = 0.0
                    departure_time_s = 0.0
                    label = f"{Fore.BLUE}START Baza  {Fore.RESET}"
                    tw_str = "-"
                    status_msg = "Wyjazd"
                else:
                    travel_time = time_matrix[route[i - 1].id][node.id]
                    arrival_time_s = current_time_s + travel_time

                    if node.id != 0:
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
                        start_service_s = arrival_time_s
                        departure_time_s = arrival_time_s
                        label = f"{Fore.BLUE}KONIEC Baza {Fore.RESET}"
                        tw_str = f"{node.time_window[0].strftime('%H:%M')}-{node.time_window[1].strftime('%H:%M')}"

                arr_str = str(timedelta(seconds=int(arrival_time_s))) if i > 0 else "-"
                start_str = str(timedelta(seconds=int(start_service_s)))
                dep_str = str(timedelta(seconds=int(departure_time_s)))

                print(f"{label:<12} | {node.demand:<5} | {current_load:<6} | {tw_str:<15} | "
                      f"{arr_str:<10} | {start_str:<15} | {dep_str:<10} | {status_msg}")

                current_time_s = departure_time_s

            grand_total_seconds += current_time_s
            print(f"{Style.DIM}--- Czas trasy: {current_time_s / 60:.2f} min ---{Style.RESET_ALL}")

        # --- STOPKA ZBIORCZA ---
        print("\n" + Fore.CYAN + "=" * 118)
        print(f"{'STATYSTYKI KOŃCOWE':^118}")
        print("-" * 118 + Style.RESET_ALL)

        # 1. SEKACJA FEROMONÓW
        if pheromone is not None:
            # Konwertujemy na numpy array na potrzeby obliczeń (zadziała dla list i dla ndarray)
            p_data = np.array(pheromone)

            p_max = np.max(p_data)
            p_min = np.min(p_data)
            p_avg = np.mean(p_data)

            print(f"  Statystyki feromonów:")
            print(f"    - Maksimum: {Fore.MAGENTA}{p_max:.6f}{Style.RESET_ALL}")
            print(f"    - Minimum:  {Fore.MAGENTA}{p_min:.6f}{Style.RESET_ALL}")
            print(f"    - Średnia:  {p_avg:.6f}")
            print("-" * 50)
        else:
            print(f"  Statystyki feromonów: {Style.DIM}Brak danych (Algorytm nieferomonowy){Style.RESET_ALL}")
            print("-" * 50)

        # 2. STATUS ODWIEDZIN
        num_visited = len(visited_client_ids)
        all_clients_visited = (num_visited == total_clients_in_problem)
        visit_color = Fore.GREEN if all_clients_visited else Fore.RED

        print(f"  Odwiedzeni klienci: {visit_color}{num_visited} / {total_clients_in_problem} "
              f"({(num_visited / total_clients_in_problem) * 100:.1f}%){Style.RESET_ALL}")

        if not overloaded_vehicles:
            print(f"  Pojemność floty:    {Fore.GREEN}OK - wszystkie pojazdy w normie{Style.RESET_ALL}")
        else:
            ids_str = ", ".join(overloaded_vehicles)
            print(f"  Pojemność floty:    {Fore.RED}{Style.BRIGHT}PRZEKROCZONA w pojazdach ID: {ids_str}{Style.RESET_ALL}")

        if not all_clients_visited:
            missing = total_clients_in_problem - num_visited
            print(f"{Back.RED}{Fore.WHITE}{Style.BRIGHT}  UWAGA: NIE ODWIEDZONO WSZYSTKICH! BRAKUJE: {missing} KLIENTÓW!  {Style.RESET_ALL}")

        print(f"  Łączny koszt czasowy floty: {Fore.YELLOW}{grand_total_seconds / 60:.2f} min{Style.RESET_ALL}")
        print(f"  Użyte pojazdy: {len([v for v in self.problem.vehicles if len(v.route) > 2])} / {len(self.problem.vehicles)}")
        print(Fore.CYAN + "=" * 118 + Style.RESET_ALL)

        return all_clients_visited and not overloaded_vehicles
