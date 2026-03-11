from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


def solve_tsp(distance_matrix):

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    route = []
    index = routing.Start(0)
    total_cost = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)

        next_index = solution.Value(routing.NextVar(index))
        next_node = manager.IndexToNode(next_index)

        # dodaj koszt krawędzi
        total_cost += distance_matrix[node][next_node]

        index = next_index

    route.append(manager.IndexToNode(index))  # powrót do depot

    return route, total_cost