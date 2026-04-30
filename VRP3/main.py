from colorama import Fore, Style, init

from VRP3.Problem.VRP import VRP

from VRP3.ACO_for_VRP_1 import ACO_for_VRP_1
from VRP3.ACO_for_VRP_2 import ACO_for_VRP_2
from VRP3.ACO_for_VRP_3 import ACO_for_VRP_3
from VRP3.ACO_for_VRP_4 import ACO_for_VRP_4
from VRP3.ACO_for_VRP_5 import ACO_for_VRP_5
from VRP3.Gready import greedy_vrp

from VRP3.Utills.Generator import Generator
from VRP3.Utills.Visualizer import Visualizer, plt
from VRP3.Utills.Summarizer import Summarizer
from VRP3.Utills.Plotter import Plotter
from VRP3.Utills.VRP_saver import VRP_saver
from VRP3.Utills.ResearchRunner import ResearchRunner
from VRP3.Utills.SummaryResearch import SummaryResearch
from VRP3.Utills.Helpers import Helpers

VISUALIZE = False
SHOW_PLOT_CONV = False
SAVE = False
RESEARCH = False
SUMMARY_RESEARCH = True
BEST_PARAMETERS_ACO_3 = False
BEST_PARAMETERS_ACO_4 = False
TEST = False

DIR_NAME = "Results"


def main():
    # Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
    init(autoreset=True)

    #  --- 1. GENERACJA DANYCH ---
    params = {
        "ants_count": 40,
        "n": 40,
        "d0": 10,
        "d1": 100,
        "t0": 0,
        "t1": 3,
        "seed": 54
    }

    dataset_name = f'Research_Dataset_{params["n"]}'

    ants_count = params["ants_count"]
    generator = Generator(d0=params["d0"], d1=params["d1"], t0=params["t0"], t1=params["t1"], n=params["n"],
                          seed=params["seed"])

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

    #  --- 2. PROBLEM VRP ---
    problem = VRP(nodes, vehicles=vehicles)
    if SAVE:
        VRP_saver.save_problem(
            dataset_name=dataset_name,
            vrp_problem=problem,
            generator_obj=generator,
            folder_name=DIR_NAME,
            subfolder_name=dataset_name,
            file_name=f"{dataset_name}_problem_def.json"
        )
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

    # Wizualizacja tras
    if VISUALIZE or SAVE:
        visualizer = Visualizer(nodes)
        visualizer.create(title="GREEDY")
        visualizer.add_routes(greedy_vehicles)
        if VISUALIZE:
            visualizer.show(block=False)
        if SAVE:
            visualizer.save(fname=VRP_saver.set_path(DIR_NAME, file_name=f"{dataset_name}_routes_greedy.png",
                                                     subfolder_name=dataset_name))

    # --- 4. BADANIA ---
    if RESEARCH:
        print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
        print(f"{'DOBÓR_PARAMETRÓW':^118}")
        print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + Style.RESET_ALL)

        solver_info_aco_4 = {
            "name": "ACO 4 (seq. with depot)",
            "save_name": "ACO_4",
            "class": ACO_for_VRP_4,
            "params": {
                "ants": ants_count,
                "iterations": 4000,
                "alpha": 999999,
                "beta": 999999,
                "evaporation": 999999,
                "patience": 999999,
                "patience_small_shake": 999999,
                "patience_big_shake": 999999,
                "big_shake_evaporation": 0.4,
                "big_shake_duration": 999999,
                "intensity_small_shake": 999999,
                "intensity_big_shake": 999999,
                "intensity_elite_ant": 0.5,
                "ranked_ants_count": (int(ants_count * 0.15), int(ants_count * 0.5)),
                "q_pheromone": 1000.0,
                "tau_min": 0.01,
                "tau_max": 10.0
            }
        }

        # solver_info_aco_3 = {
        #     "name": "ACO 3 (seq.)",
        #     "save_name": "ACO_3",
        #     "class": ACO_for_VRP_3,
        #     "params": {
        #         "ants": ants_count,
        #         "iterations": 4000,
        #         "alpha": 999999,
        #         "beta": 999999,
        #         "evaporation": 999999,
        #         "patience": 999999,
        #         "patience_small_shake": 999999,
        #         "patience_big_shake": 999999,
        #         "big_shake_evaporation": 0.4,
        #         "big_shake_duration": 999999,
        #         "intensity_small_shake": 999999,
        #         "intensity_big_shake": 999999,
        #         "intensity_elite_ant": 0.5,
        #         "ranked_ants_count": (int(ants_count * 0.15), int(ants_count * 0.5)),
        #         "q_pheromone": 1000.0,
        #         "tau_min": 0.01,
        #         "tau_max": 10.0
        #     }
        # }

        research_runner = ResearchRunner(solver_info=solver_info_aco_4,
                                         folder_name=DIR_NAME, subfolder_name=dataset_name)
        best_vehicles, best_cost, history = research_runner.run_experiment(problem=problem.copy(), repeats=10)

        # Plotowanie najlepszego wyniku
        plotter = Plotter()
        plotter.plot_single_aco(
            name=solver_info_aco_4["name"],
            history=history,
            greedy_baseline=greedy_cost,
            save=True,  # Flaga zapisu
            show=SHOW_PLOT_CONV,
            folder_name="Results",
            subfolder_name=dataset_name,
            file_name=f"{dataset_name}_conv_{solver_info_aco_4['save_name']}",
        )

        exit(0)

    # --- 5. PODSUMOWANIE BADAŃ - POSZUKIWANIA PARAMETRÓW ---
    if SUMMARY_RESEARCH:
        print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
        print(f"{'PODSUMOWANIE BADAŃ':^118}")
        print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + Style.RESET_ALL)

        print("\n" + Fore.CYAN + Style.BRIGHT + "-" * 118)
        print(f"{'ACO 3':^118}")
        SummaryResearch.aggregate(folder_name=DIR_NAME, subfolder_name=dataset_name,
                                  file_name="research_dataset_ACO_3_C39_A40_R10")

        print("\n" + Fore.CYAN + Style.BRIGHT + "-" * 118)
        print(f"{'ACO 4':^118}")
        SummaryResearch.aggregate(folder_name=DIR_NAME, subfolder_name=dataset_name,
                                  file_name="research_dataset_ACO_4_C39_A40_R10")

    # --- 6. WYBÓR NAJLEPSZEGO ZESTAWU PARAMETRÓW ---
    # TU: wybrać najlepszy zestaw parametrów i zapisać do pliku
    if SUMMARY_RESEARCH:
        print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
        print(f"{'WYBÓR NAJLEPSZYCH PARAMETRÓW':^118}")
        print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + Style.RESET_ALL)

        print("\n" + Fore.CYAN + Style.BRIGHT + "-" * 118)
        print(f"{'ACO 3':^118}")

        # KOD DO WYBORU NAJLEPSZYCH PARAM

        print("\n" + Fore.CYAN + Style.BRIGHT + "-" * 118)
        print(f"{'ACO 4':^118}")

        # KOD DO WYBORU NAJLEPSZYCH PARAM

        exit(0)

    # --- 7. ACO - PARAMETRY ---
    plotter = Plotter()

    aco_configs = []

    if BEST_PARAMETERS_ACO_3:

        # ODCZYT NAJLEPSZYCH PARAMETRÓW ACO_3 Z PLIKU

        exit()
    else:
        aco_configs.append({
            "name": "ACO 3 (seq.)",
            "save_name": "ACO_3",
            "class": ACO_for_VRP_3,
            "params": {"ants": ants_count, "iterations": 50, "alpha": 1, "beta": 5, "evaporation": 0.05,
                       "patience": 200}
            })

    if BEST_PARAMETERS_ACO_4:

        # ODCZYT NAJLEPSZYCH PARAMETRÓW ACO_4 Z PLIKU

        exit()
    else:
        aco_configs.append({
            "name": "ACO 4 (seq. with depot)",
            "save_name": "ACO_4",
            "class": ACO_for_VRP_4,
            "params": {"ants": ants_count, "iterations": 50, "alpha": 1, "beta": 2, "evaporation": 0.08,
                       "patience": 500, "patience_small_shake": 11190, "patience_big_shake": 111250,
                       "big_shake_evaporation": 0.4, "big_shake_duration": 50,
                       "intensity_small_shake": 0.1, "intensity_big_shake": 0.6,
                       "intensity_elite_ant": 0.5,
                       "ranked_ants_count": (int(ants_count * 0.15), int(ants_count * 0.5)),
                       "q_pheromone": 1000.0, "tau_min": 0.01, "tau_max": 10.0}
            })

    # --- 8. ACO - POJEDYNCZY TEST ---

    # --- PĘTLA TESTUJĄCA ---
    for config in aco_configs:
        name = config["name"]
        save_name = config["save_name"]
        ACO_Class = config["class"]  # Dynamiczne przypisanie klasy
        params = config["params"]

        print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
        print(f"{name.upper():^118}")
        print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + "\n")

        # Inicjalizacja instancji konkretnej klasy
        aco_instance = ACO_Class(
            problem.copy(),
            **params
        )

        # Uruchomienie
        vehicles, cost, history = aco_instance.run()

        # 2. Plotowanie
        plotter.plot_single_aco(
            name=config["name"],
            history=history,
            greedy_baseline=greedy_cost,
            save=True,  # Flaga zapisu
            show=SHOW_PLOT_CONV,
            folder_name=DIR_NAME,
            subfolder_name=dataset_name,
            file_name=f"{dataset_name}_conv_{config['save_name']}"
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

        # Wizualizacja tras
        if VISUALIZE or SAVE:
            visualizer = Visualizer(nodes)
            visualizer.create(name)
            visualizer.add_routes(vehicles)
            if VISUALIZE:
                visualizer.show(block=False)
            if SAVE:
                visualizer.save(fname=VRP_saver.set_path(DIR_NAME, file_name=f"{dataset_name}_routes_{save_name}.png",
                                                         subfolder_name=dataset_name))

        VRP_saver.save_aco(
            aco_cfg=config,
            vehicles=vehicles,
            cost=cost,
            folder_name=DIR_NAME,
            subfolder_name=dataset_name,
            file_name=f"{dataset_name}_{save_name}_results.json",
            verbose=True
        )
        VRP_saver.save_history(
            history=history,
            folder_name=DIR_NAME,
            subfolder_name=dataset_name,
            file_name=f"{dataset_name}_{save_name}_history.json",
            verbose=False
        )

    # --- 9. FINALNE PORÓWNANIE ZBIORCZE ---

    # DO ZMIANY POD TESTY

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
    if VISUALIZE:
        plt.show(block=True)
