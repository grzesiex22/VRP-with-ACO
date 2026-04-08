from VRP2.Generator import Generator
from VRP2.VRP import VRP
from VRP2.ACO_for_VRP import ACO_for_VRP
from VRP2.Visualizer import Visualizer, plt
from VRP2.VRP_solver import solve_vrp


def main():
    max_capacity = 400

    # 1️⃣ generowanie klientów
    generator = Generator(d0=10, d1=100, t0=0, t1=4, n=10, seed=50)
    nodes, vehicles = generator.generate()

    print("\nWygenerowane punkty:")
    for node in nodes:
        print(node)

    print("\n"), print("-" * 100)
    print("\nWygenerowane pojazdy\n")
    for v in vehicles:
        print(v)
    print("\n"), print("-" * 100)

    # 2️⃣ stworzenie problemu VRP
    problem = VRP(nodes, max_capacity=max_capacity, vehicles=vehicles)

    # 3️⃣ uruchomienie algorytmu mrówkowego
    aco = ACO_for_VRP(problem, ants=10, iterations=100)

    best_vehicles, best_cost = aco.run()

    # 4️⃣ wyniki
    print("\nWłasne VRP - Najlepsza trasa:")
    best_route = [v.routes for v in best_vehicles]
    indices = [[node.id for node in route] for route in best_route]
    for i, route in enumerate(indices):
        print(f"id={i} filled={best_vehicles[i].filling}/{best_vehicles[i].capacity} \n\troute: ", end="")
        print(" -> ".join(map(str, route)))

    print(f"\nWłasny czas trasy: {best_cost/60} minut")

    # Wyświetlenie szczegółów
    aco.print_summary(best_vehicles)

    visualizer = Visualizer(nodes)
    visualizer.show(best_route, title="WŁASNY")

    # 5 OR-TOOLS
    optimal_vehicles, optimal_cost = solve_vrp(
        nodes,
        problem.time_matrix_seconds,
        vehicles
    )
    print("\n"), print("-" * 100)
    print("\nOR-Tools - VRP  - Najlepsza trasa:")
    optimal_routes = [v.routes for v in optimal_vehicles]
    indices = [[node.id for node in route] for route in optimal_routes]
    for i, route in enumerate(indices):
        print(f"id={i} filled={optimal_vehicles[i].filling}/{optimal_vehicles[i].capacity} \n\troute: ", end="")
        print(" -> ".join(map(str, route)))
    
    print(f"\nOR-Tools cost: {optimal_cost/60} minut")

    # Wyświetlenie szczegółów
    aco.print_summary(optimal_vehicles)

    visualizer.show(optimal_routes, title="OR-TOOLS")


if __name__ == "__main__":
    main()
    plt.show(block=True)
