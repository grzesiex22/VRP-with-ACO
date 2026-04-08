from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import sys


MAX_TIME = 72 * 3600


def solve_vrp(nodes, distance_matrix, vehicle_count, vehicle_capacity):
    demands = [node.demand for node in nodes]

    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),
        vehicle_count,
        0  # depot
    )

    routing = pywrapcp.RoutingModel(manager)

    # koszt przejazdu
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)

        if from_index < 0 or to_index < 0:
            raise ValueError(f"Zły index w callbacku: {from_index}, {to_index}")

        travel = distance_matrix[from_node][to_node]
        service = nodes[from_node].service_s

        return int(travel + service)

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(time_callback_index)

    routing.AddDimension(
        time_callback_index,
        MAX_TIME,  # duży slack, żeby solver mógł się spóźniać
        MAX_TIME,  # max czas trasy
        False,  # nie wymuszaj startu od 0
        "Time"
    )
    time_dimension = routing.GetDimensionOrDie("Time")

    for i, node in enumerate(nodes):
        index = manager.NodeToIndex(i)

        # kara za przyjechanie za wcześnie
        earliest = int(node.time_window_s[0])

        if i == 0:
            earliest = 0
            latest = MAX_TIME
            penalty = 0
        else:
            earliest = int(node.time_window_s[0])
            latest = int(node.time_window_s[1])
            penalty = int(node.penalty_s[1])

        time_dimension.CumulVar(index).SetRange(earliest, MAX_TIME)
        time_dimension.SetCumulVarSoftUpperBound(index, latest, penalty)

    time_dimension.SetGlobalSpanCostCoefficient(1)

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
    current_time_s = 0

    for vehicle_id in range(vehicle_count):

        index = routing.Start(vehicle_id)
        route = []

        while not routing.IsEnd(index):

            id = manager.IndexToNode(index)
            route.append(nodes[id])

            next_index = solution.Value(routing.NextVar(index))
            next_id = manager.IndexToNode(next_index)

            if id == next_id:
                break

            # total_cost += distance_matrix[node][next_node]
            current_time_s += int(distance_matrix[id][next_id])

            # dodatkowy czas za spóźnienie
            if current_time_s > nodes[next_id].time_window_s[1]:
                current_time_s += int(nodes[next_id].penalty_s[1])

            # czekanie na otwarcie
            elif current_time_s < nodes[next_id].time_window_s[0]:
                wait_time = nodes[next_id].time_window_s[0] - current_time_s
                current_time_s += int(wait_time)

            # czas obsługi
            current_time_s += int(nodes[next_id].service_s)

            index = next_index

        route.append(nodes[manager.IndexToNode(index)])

        if len(route) > 2:
            routes.append(route)

    total_cost = solution.ObjectiveValue()
    print(f"MANUAL: {current_time_s}, OBJ_VAL: {total_cost}\n")

    return routes, total_cost