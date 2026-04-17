from colorama import Fore, Back, Style, init

from VRP3.Generator import Generator
from VRP3.VRP import VRP
from VRP3.ACO_for_VRP_1 import ACO_for_VRP_1
from VRP3.ACO_for_VRP_2 import ACO_for_VRP_2
from VRP3.ACO_for_VRP_3 import ACO_for_VRP_3
from VRP3.ACO_for_VRP_4 import ACO_for_VRP_4
from VRP3.Visualizer import Visualizer, plt
from VRP3.Gready import greedy_vrp


VISUALIZE = True


def main():
    # Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
    init(autoreset=True)

    #  --- 1. GENERACJA DANYCH ---
    generator = Generator(d0=10, d1=100, t0=0, t1=5, n=5, seed=54)
    # generator = Generator(d0=10, d1=100, t0=0, t1=5, n=5, seed=50)

    nodes, vehicles = generator.generate()

    # --- Wygenerowane punkty ---
    print("\n" + Fore.LIGHTYELLOW_EX + "#" * 118)
    print(f"{'Wygenerowane punkty':^118}")
    print("-" * 118 + Style.RESET_ALL)

    for node in nodes:
        print(node)

    # --- Wygenerowane pojazdy ---
    print(Fore.LIGHTYELLOW_EX + "#" * 118)
    print(f"{'Wygenerowane pojazdy':^118}")
    print("-" * 118 + Style.RESET_ALL)

    for v in vehicles:
        print(v)

    print(Fore.LIGHTYELLOW_EX + "#" * 118 + Style.RESET_ALL)

    #  --- 2. stworzenie problemu VRP ---
    problem = VRP(nodes, vehicles=vehicles)

    # --- 3. ACO ---
    aco_configs = [
        {
            "name": "ACO 1 (without constraints)",
            "class": ACO_for_VRP_1,
            "params": {"ants": 100, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 300}
        },
        {
            "name": "ACO 2 (seq.)",
            "class": ACO_for_VRP_2,
            "params": {"ants": 100, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 300}
        },
        {
            "name": "ACO 3 (seq. with local search)",
            "class": ACO_for_VRP_3,
            "params": {"ants": 100, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 300}
        },
        # {
        #     "name": "ACO 4 (seq. wersja grzesia)",
        #     "class": ACO_for_VRP_4,
        #     "params": {"ants": 100, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 300}
        # }
    ]

    # Słownik do przechowywania wyników dla tabeli końcowej
    results_summary = {}

    # --- PĘTLA TESTUJĄCA ---
    for config in aco_configs:
        name = config["name"]
        ACO_Class = config["class"]  # Dynamiczne przypisanie klasy
        p = config["params"]

        print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
        print(f"{name.upper():^118}")
        print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + "\n")

        # Inicjalizacja instancji konkretnej klasy
        aco_instance = ACO_Class(
            problem,
            ants=p["ants"],
            iterations=p["iter"],
            alpha=p["alpha"],
            beta=p["beta"],
            evaporation=p["evap"]
        )

        # Uruchomienie
        vehicles, cost = aco_instance.run(patience=p["patience"])

        # Przechowywanie wyników
        results_summary[name] = {"cost": cost, "vehicles": vehicles}

        # Podgląd tras w konsoli
        print(f"\n{name} - Najlepsza trasa:")
        for v in vehicles:
            if len(v.route) > 2:
                route_ids = [n.id for n in v.route]
                print(f"  Pojazd {v.id}: {' -> '.join(map(str, route_ids))} ({v.filling}/{v.capacity})")

        # Szczegółowe podsumowanie z kolorami
        # (Metoda print_summary powinna zwracać True/False jeśli to możliwe)
        is_ok = problem.print_summary(vehicles)
        results_summary[name]["is_ok"] = is_ok

        if VISUALIZE:
            visualizer = Visualizer(nodes)
            visualizer.show([v.route for v in vehicles], title=name)

    # --- 4. ALGORYTM GREEDY (Punkt odniesienia) ---
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
    print(f"{'ALGORYTM GREADY':^118}")
    print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + Style.RESET_ALL)

    greedy_vehicles, greedy_cost = greedy_vrp(nodes, problem.time_matrix_seconds, problem.vehicles)
    is_greedy_ok = problem.print_summary(greedy_vehicles)
    results_summary["GREEDY"] = {"cost": greedy_cost, "vehicles": greedy_vehicles, "is_ok": is_greedy_ok}

    # - Szybki podgląd tras
    print("\nGready  - VRP  - Najlepsza trasa:")
    optimal_routes = [v.route for v in greedy_vehicles]
    indices = [[node.id for node in route] for route in optimal_routes]
    for i, route in enumerate(indices):
        print(f"id={i} filled={greedy_vehicles[i].filling}/{greedy_vehicles[i].capacity} \n\troute: ", end="")
        print(" -> ".join(map(str, route)))

    print(f"\nGREEDY czas trasy:" + Fore.YELLOW + f"{greedy_cost/60} minut" + Style.RESET_ALL)

    # - Wyświetlenie szczegółów
    greedy_ok = problem.print_summary(greedy_vehicles)

    if VISUALIZE:
        visualizer = Visualizer(nodes)
        visualizer.show(optimal_routes, title="GREEDY")

    # --- 5. FINALNE PORÓWNANIE ZBIORCZE ---
    print("\n" + Fore.LIGHTGREEN_EX + Style.BRIGHT + "#" * 118)
    print(f"{'TABELA PORÓWNAWCZA WYNIKÓW':^118}")
    print("-" * 118)

    # Nagłówki tabeli
    print(f"{'Nazwa Algorytmu':<25} | {'Koszt [min]':<15} | {'Status':<15} | {'Użyte auta':<10}")
    print("-" * 118)

    for name, res in results_summary.items():
        cost_min = res["cost"] / 60
        status_text = "OK" if res["is_ok"] else "BŁĄD/KARY"
        status_color = Fore.GREEN if res["is_ok"] else Fore.RED

        # Liczymy tylko pojazdy, które faktycznie wyjechały
        used_v = len([v for v in res["vehicles"] if len(v.route) > 2])

        # Wyróżnienie najlepszego wyniku (najmniejszego kosztu)
        # Szukamy minimum tylko wśród poprawnych (res["is_ok"])
        is_best = False  # (Tu można dodać logikę szukania najlepszego)

        print(f"{name:<25} | {Fore.YELLOW}{cost_min:>10.2f} min{Style.RESET_ALL} | "
              f"{status_color}{status_text:<15}{Style.RESET_ALL} | {used_v:>5}")

    print(Fore.LIGHTGREEN_EX + "#" * 118 + Style.RESET_ALL)


if __name__ == "__main__":
    main()
    plt.show(block=True)
