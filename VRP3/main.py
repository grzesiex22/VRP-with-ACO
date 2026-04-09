from colorama import Fore, Back, Style, init


from VRP3.Generator import Generator
from VRP3.VRP import VRP
from VRP3.ACO_for_VRP import ACO_for_VRP
from VRP3.Visualizer import Visualizer, plt
from VRP3.VRP_solver import solve_vrp
from VRP3.Gready import greedy_vrp


VISUALIZE = True

def main():
    # Inicjalizacja colorama (wymagana na Windowsie, by kody działały)
    init(autoreset=True)

    # 1️⃣ generowanie klientów
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

    # 2️⃣ stworzenie problemu VRP
    problem = VRP(nodes, vehicles=vehicles)

    # 3️⃣ uruchomienie algorytmu mrówkowego
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
    print(f"{'ALGORYTM MRÓWKOWY':^118}")
    print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + "\n" + Style.RESET_ALL)

    aco = ACO_for_VRP(problem, ants=100, iterations=1000, alpha=1, beta=2, evaporation=0.05)

    aco_vehicles, ACO_cost = aco.run(patience=300)

    # 4️⃣ wyniki
    print("\nWłasne VRP - Najlepsza trasa:")
    best_route = [v.route for v in aco_vehicles]
    indices = [[node.id for node in route] for route in best_route]
    for i, route in enumerate(indices):
        print(f"id={i} filled={aco_vehicles[i].filling}/{aco_vehicles[i].capacity} \n\troute: ", end="")
        print(" -> ".join(map(str, route)))

    print(f"\nWłasny czas trasy:" + Fore.YELLOW + f"{ACO_cost/60} minut" + Style.RESET_ALL)

    # Wyświetlenie szczegółów
    aco_ok = problem.print_summary(aco_vehicles)

    if VISUALIZE:
        visualizer = Visualizer(nodes)
        visualizer.show(best_route, title="WŁASNY")

    # 5 GREEDY
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "#" * 118)
    print(f"{'ALGORYTM GREADY':^118}")
    print(Fore.MAGENTA + Style.BRIGHT + "#" * 118 + Style.RESET_ALL)

    greedy_vehicles, GREEDY_cost = greedy_vrp(nodes, problem.time_matrix_seconds, problem.vehicles)
    print("\nGready  - VRP  - Najlepsza trasa:")
    optimal_routes = [v.route for v in greedy_vehicles]
    indices = [[node.id for node in route] for route in optimal_routes]
    for i, route in enumerate(indices):
        print(f"id={i} filled={greedy_vehicles[i].filling}/{greedy_vehicles[i].capacity} \n\troute: ", end="")
        print(" -> ".join(map(str, route)))

    print(f"\nGREEDY czas trasy:" + Fore.YELLOW + f"{GREEDY_cost/60} minut" + Style.RESET_ALL)

    # Wyświetlenie szczegółów
    greedy_ok = problem.print_summary(greedy_vehicles)

    if VISUALIZE:
        visualizer = Visualizer(nodes)
        visualizer.show(optimal_routes, title="GREEDY")

    # --- PORÓWNANIE ---
    print("\n" + Fore.LIGHTGREEN_EX + "#" * 118)
    print(f"{'PORÓWNANIE':^118}")
    print("-" * 118 + Style.RESET_ALL)
    style_aco_ok = Fore.GREEN if aco_ok else Fore.RED
    print(f"Własny czas trasy:" + style_aco_ok + f"{ACO_cost/60} minut" + Style.RESET_ALL)
    # print(f"OR-Tools cost: {GREEDY_cost / 60} minut")
    style_greedy_ok = Fore.GREEN if greedy_ok else Fore.RED
    print(f"GREEDY czas trasy:" + style_greedy_ok + f"{GREEDY_cost/60} minut" + Style.RESET_ALL)

    print(Fore.LIGHTGREEN_EX + "#" * 118 + Style.RESET_ALL)


if __name__ == "__main__":
    main()
    plt.show(block=True)
