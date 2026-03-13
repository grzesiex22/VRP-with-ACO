from VRP.Generator import Generator
from VRP.VRP import VRP
from VRP.ACO_for_VRP import ACO_for_VRP
from VRP.Visualizer import Visualizer , plt
from VRP.VRP_solver import solve_vrp


def main():
    max_capacity = 1500

    # 1️⃣ generowanie klientów
    generator = Generator(n=15, seed=50)
    nodes = generator.generate()

    print("Wygenerowane punkty:")
    for node in nodes:
        print(f"id={node.id} x={node.x} y={node.y} d={node.demand}")

    # 2️⃣ stworzenie problemu VRP
    problem = VRP(nodes, max_capacity=max_capacity)

    # 3️⃣ uruchomienie algorytmu mrówkowego
    aco = ACO_for_VRP(problem, ants=30, iterations=100)

    best_route, best_cost = aco.run()

    # 4️⃣ wyniki
    print("\nVRP - Najlepsza trasa:")
    for route in best_route:
        print(" -> ".join(map(str, route)))

    print("\nKoszt trasy:")
    print(best_cost)
    visualizer = Visualizer(nodes)
    visualizer.show(best_route, title="WŁASNY")

    # 5 OR-TOOLS
    optimal_routes, optimal_cost = solve_vrp(
        nodes,
        problem.dist_matrix,
        vehicle_count=len(problem.nodes) - 1,
        vehicle_capacity=max_capacity
    )

    print("\nOR-Tools - VRP  - Najlepsza trasa:")
    for route in optimal_routes:
        print(" -> ".join(map(str, route)))

    print("OR-Tools cost:", optimal_cost)
    visualizer.show(optimal_routes, title="OR-TOOLS")


if __name__ == "__main__":
    main()
    plt.show(block=True)
