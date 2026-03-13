from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


def solve_vrp(nodes, distance_matrix, vehicle_count, vehicle_capacity):

    demands = [node.demand for node in nodes]

    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),
        vehicle_count,
        0  # depot
    )

    routing = pywrapcp.RoutingModel(manager)

    # koszt przejazdu
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        return int(distance_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # demand klientów
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [vehicle_capacity] * vehicle_count,
        True,
        "Capacity"
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    search_parameters.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_parameters)

    if solution is None:
        return None, None

    routes = []
    total_cost = 0

    for vehicle_id in range(vehicle_count):

        index = routing.Start(vehicle_id)
        route = []

        while not routing.IsEnd(index):

            node = manager.IndexToNode(index)
            route.append(node)

            next_index = solution.Value(routing.NextVar(index))
            next_node = manager.IndexToNode(next_index)

            total_cost += distance_matrix[node][next_node]

            index = next_index

        route.append(manager.IndexToNode(index))

        if len(route) > 2:
            routes.append(route)

    return routes, total_cost