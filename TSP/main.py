from TSP.Generator import Generator
from TSP.TSP import TSP
from TSP.ACO_for_TSP import ACO_for_TSP
from TSP.Visualizer import Visualizer
from TSP.TSP_solver import solve_tsp


def main():

    # 1️⃣ generowanie klientów
    generator = Generator(n=10)
    nodes = generator.generate()

    print("Wygenerowane punkty:")
    for node in nodes:
        print(f"id={node.id} x={node.x} y={node.y}")

    # 2️⃣ stworzenie problemu VRP
    problem = TSP(nodes)

    # 3️⃣ uruchomienie algorytmu mrówkowego
    aco = ACO_for_TSP(problem, ants=10, iterations=100)

    best_route, best_cost = aco.run()

    # 4️⃣ wyniki
    print("\nNajlepsza trasa:")
    print(best_route)
    print("\nKoszt trasy:")
    print(best_cost)
    visualizer = Visualizer(nodes)
    visualizer.show(best_route)

    optimal_route, optimal_cost = solve_tsp(problem.dist_matrix)
    print("\nOR-Tools trasa:")
    print(optimal_route)
    print("\nKoszt trasy:")
    print(optimal_cost)
    visualizer.show(optimal_route)



if __name__ == "__main__":
    main()