from colorama import Fore, Back, Style, init

from VRP3.Generator import Generator
from VRP3.VRP import VRP

from VRP3.ACO_for_VRP_1 import ACO_for_VRP_1
from VRP3.ACO_for_VRP_2 import ACO_for_VRP_2
from VRP3.ACO_for_VRP_3 import ACO_for_VRP_3
from VRP3.ACO_for_VRP_4 import ACO_for_VRP_4
from VRP3.ACO_for_VRP_5 import ACO_for_VRP_5

from VRP3.Visualizer import Visualizer, plt
from VRP3.Summarizer import Summarizer
from VRP3.Gready import greedy_vrp
from VRP3.Plotter import Plotter


VISUALIZE = True
SHOW_PLOT_CONV = False
DATASET = "Dataset_01"


def main():
    # Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
    init(autoreset=True)

    #  --- 1. GENERACJA DANYCH ---
    ants_count = 20
    generator = Generator(d0=10, d1=100, t0=0, t1=5, n=20, seed=54)
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

    results_summary = {}  # Słownik do przechowywania wyników dla tabeli końcowej

    # --- 3. ALGORYTM GREEDY (Punkt odniesienia) ---
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
    print(f"{'ALGORYTM GREADY':^118}")
    print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + Style.RESET_ALL)

    gready_problem, greedy_cost = greedy_vrp(nodes, problem.copy())
    greedy_vehicles = gready_problem.vehicles
    summarizer = Summarizer(gready_problem)
    is_greedy_ok = summarizer.generate_summary()

    results_summary["GREEDY"] = {"cost": greedy_cost, "vehicles": greedy_vehicles, "is_ok": is_greedy_ok}

    # - Szybki podgląd tras
    print("\nGready  - VRP  - Najlepsza trasa:")
    optimal_routes = [v.route for v in greedy_vehicles]
    indices = [[node.id for node in route] for route in optimal_routes]
    for i, route in enumerate(indices):
        print(f"id={i} filled={greedy_vehicles[i].filling}/{greedy_vehicles[i].capacity} \n\troute: ", end="")
        print(" -> ".join(map(str, route)))

    print(f"\nGREEDY czas trasy:" + Fore.YELLOW + f"{greedy_cost/60} minut" + Style.RESET_ALL)

    if VISUALIZE:
        visualizer = Visualizer(nodes)
        visualizer.show(optimal_routes, title="GREEDY")

    # --- 4. ACO ---
    plotter = Plotter()
    aco_configs = [
        {
            "name": "ACO 1 (without constraints)",
            "class": ACO_for_VRP_1,
            "params": {"ants": ants_count, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 200}
        },
        {
            "name": "ACO 2 (seq.)",
            "class": ACO_for_VRP_2,
            "params": {"ants": ants_count, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 200}
        },
        {
            "name": "ACO 3 (seq. with local search)",
            "class": ACO_for_VRP_3,
            "params": {"ants": ants_count, "iter": 1000, "alpha": 1, "beta": 2, "evap": 0.05, "patience": 200}
        },
        {
            "name": "ACO 4 (seq. with depot)",
            "class": ACO_for_VRP_4,
            "params": {"ants": ants_count, "iter": 1000, "alpha": 2, "beta": 2, "evap": 0.05, "patience": 200}
        },
        {
            "name": "ACO 5 (seq. with depot & gready)",
            "class": ACO_for_VRP_5,
            "params": {"ants": ants_count, "iter": 1000, "alpha": 2, "beta": 2, "evap": 0.05, "patience": 800}
        }
    ]

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
            problem.copy(),
            ants=p["ants"],
            iterations=p["iter"],
            alpha=p["alpha"],
            beta=p["beta"],
            evaporation=p["evap"]
        )

        # Uruchomienie
        vehicles, cost, history = aco_instance.run(patience=p["patience"])

        # 2. Plotowanie
        plotter.plot_single_aco(
            name=config["name"],
            history=history,
            greedy_baseline=greedy_cost,
            save=True,  # Flaga zapisu
            show=SHOW_PLOT_CONV,
            dataset=DATASET  # Twoja własna nazwa początkowa
        )

        # Podgląd tras w konsoli
        print(f"\n{name} - Najlepsza trasa:")
        for v in vehicles:
            if len(v.route) > 2:
                route_ids = [n.id for n in v.route]
                print(f"  Pojazd {v.id}: {' -> '.join(map(str, route_ids))} ({v.filling}/{v.capacity})")

        # Szczegółowe podsumowanie
        summarizer = Summarizer(aco_instance.problem)
        is_ok = summarizer.generate_summary(aco_instance.pheromone)

        # Przechowywanie wyników
        results_summary[name] = {"cost": cost, "vehicles": vehicles, "is_ok": is_ok}

        if VISUALIZE:
            visualizer = Visualizer(nodes)
            visualizer.show([v.route for v in vehicles], title=name)

    # --- 5. FINALNE PORÓWNANIE ZBIORCZE ---
    # Obliczamy minimalny koszt (tylko dla poprawnych rozwiązań 'is_ok')
    valid_costs = [res["cost"] for res in results_summary.values() if res["is_ok"]]
    min_cost = min(valid_costs) if valid_costs else float('inf')

    # Obliczamy maksymalną liczbę pojazdów, aby wiedzieć, ile kolumn narysować
    max_v_count = len(problem.vehicles)
    line_width = 67 + (max_v_count * 22)  # Dynamiczna szerokość linii

    print("\n" + Fore.LIGHTGREEN_EX + Style.BRIGHT + "#" * line_width)
    print(f"{'TABELA PORÓWNAWCZA WYNIKÓW':^{line_width}}")
    print("-" * line_width)

    # Nagłówki tabeli (Nazwa, Koszt, Status + Kolumny dla aut)
    header = f"{'Nazwa Algorytmu':<35} | {'Koszt [min]':<11} | {'Status':<8} |"
    for i in range(max_v_count):
        veh_str = f"Pojazd {i}"
        header += f" {veh_str:<14} |"
    print(header)
    print("-" * line_width)

    for name, res in results_summary.items():
        cost_min = res["cost"] / 60
        # Sprawdzamy czy ten algorytm jest zwycięzcą (uwzględniając błąd zaokrągleń)
        is_winner = res["is_ok"] and abs(res["cost"] - min_cost) < 1e-6

        status_text = "OK" if res["is_ok"] else "NOK"
        status_color = Fore.GREEN if res["is_ok"] else Fore.RED

        # --- LOGIKA WYRÓWNANIA I KOLOROWANIA ---
        # Używamy stałego prefiksu (3 znaki wizualne), aby uniknąć przesuwania kolumny
        icon_prefix = "🏆 " if is_winner else "   "

        if is_winner:
            display_name = f"🏆 {name}"
            n_style = Fore.GREEN + Style.BRIGHT
            c_style = Fore.GREEN + Style.BRIGHT
            name_padding = 34
        else:
            display_name = f"   {name}"
            n_style = Fore.WHITE
            c_style = Fore.YELLOW
            name_padding = 35

        # Tworzymy wiersz - padding :<35 musi być zastosowany do czystego stringa przed kolorami
        name_col = f"{n_style}{display_name:<{name_padding}}{Style.RESET_ALL}"
        cost_col = f"{c_style}{cost_min:>11.2f}{Style.RESET_ALL}"
        stat_col = f"{status_color}{status_text:<8}{Style.RESET_ALL}"

        row = f"{name_col} | {cost_col} | {stat_col} |"

        # Dane dla każdego pojazdu
        for i in range(max_v_count):
            if i < len(res["vehicles"]):            # Liczba klientów (bez bazy na początku i końcu)
                v = res["vehicles"][i]
                client_count = max(0, len(v.route) - 2)

                # Kolorystyka zapełnienia
                v_color = Fore.GREEN if v.filling <= v.capacity else Fore.RED
                if client_count == 0: v_color = Style.DIM  # Szary dla nieużywanych aut

                # Formatowanie: K (Klienci), Z (Zapełnienie)
                v_info = f"K:{client_count:<2} Z:{v.filling:>3}/{v.capacity}"
                row += f" {v_color}{v_info:<14}{Style.RESET_ALL} |"
            else:
                row += f" {'-':^14} |"
        print(row)

    print(Fore.LIGHTGREEN_EX + "#" * line_width + Style.RESET_ALL)


if __name__ == "__main__":
    main()
    plt.show(block=True)
