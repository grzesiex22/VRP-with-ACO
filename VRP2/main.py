from VRP2.Generator import Generator
from VRP2.VRP import VRP
from VRP2.ACO_for_VRP import ACO_for_VRP
from VRP2.Visualizer import Visualizer, plt
from VRP2.VRP_solver import solve_vrp


def main():
    max_capacity = 400

    # 1️⃣ generowanie klientów
    generator = Generator(d0=10, d1=100, t0=0, t1=4, n=4, seed=50)
    nodes = generator.generate()

    print("Wygenerowane punkty:")
    for node in nodes:
        print(f"id={node.id} x={node.x} y={node.y} d={node.demand} t={node.time_window}, s={node.service}")

    # 2️⃣ stworzenie problemu VRP
    problem = VRP(nodes, max_capacity=max_capacity)

    # 3️⃣ uruchomienie algorytmu mrówkowego
    aco = ACO_for_VRP(problem, ants=10, iterations=100)

    best_route, best_cost = aco.run()

    # 4️⃣ wyniki
    print("\nVRP - Najlepsza trasa:")
    indices = [[node.id for node in route] for route in best_route]
    for route in indices:
        print(" -> ".join(map(str, route)))

    print(f"\nWłasny czas trasy: {best_cost/60} minut")
    visualizer = Visualizer(nodes)
    visualizer.show(best_route, title="WŁASNY")

    # 5 OR-TOOLS
    optimal_routes, optimal_cost = solve_vrp(
        nodes,
        problem.time_matrix_seconds,
        vehicle_count=len(problem.nodes) - 1,
        vehicle_capacity=max_capacity
    )
    
    print("\nOR-Tools - VRP  - Najlepsza trasa:")
    indices = [[node.id for node in route] for route in optimal_routes]
    for route in indices:
        print(" -> ".join(map(str, route)))
    
    print(f"\nOR-Tools cost: {optimal_cost/60} minut")
    visualizer.show(optimal_routes, title="OR-TOOLS")


if __name__ == "__main__":
    main()
    plt.show(block=True)
