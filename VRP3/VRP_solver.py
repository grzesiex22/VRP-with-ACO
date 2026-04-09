from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import sys


MAX_TIME = 72 * 3600


def solve_vrp(nodes, distance_matrix, vehicles):
    # 1. Skalowanie dla zachowania precyzji (sekundy -> milisekundy)
    # OR-Tools nie lubi floatów, więc mnożymy wszystko przez 100
    SCALE = 100
    vehicle_count = len(vehicles)
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), vehicle_count, 0)
    routing = pywrapcp.RoutingModel(manager)

    # 2. Poprawiony Callback czasu (z uwzględnieniem skali)
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # Czas przejazdu + serwis w punkcie startowym
        travel = distance_matrix[from_node][to_node]
        service = nodes[from_node].service_s
        return int((travel + service) * SCALE)

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 3. Wymiar czasu
    routing.AddDimension(transit_callback_index, MAX_TIME * SCALE, MAX_TIME * SCALE, False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")

    for i, node in enumerate(nodes):
        index = manager.NodeToIndex(i)
        if i == 0:
            time_dimension.CumulVar(index).SetRange(0, MAX_TIME * SCALE)
        else:
            # Okna czasowe też skalujemy
            earliest = int(node.time_window_s[0] * SCALE)
            latest = int(node.time_window_s[1] * SCALE)
            # Kara w OR-Tools (SoftUpperBound) nie przesuwa czasu,
            # więc użyjemy jej tylko do optymalizacji, a czas policzymy ręcznie poniżej
            time_dimension.CumulVar(index).SetRange(earliest, MAX_TIME * SCALE)
            # routing.GetMutableResources()  # opcjonalne
            time_dimension.SetCumulVarSoftUpperBound(index, latest, int(node.penalty_s[1] * SCALE))

    # 4. Callback ładunku (Demand)
    def demand_callback(from_index):
        return nodes[manager.IndexToNode(from_index)].demand

    demand_id = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(demand_id, 0, [v.capacity for v in vehicles], True, "Capacity")

    # 5. Rozwiązanie
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 2

    solution = routing.SolveWithParameters(search_parameters)
    if not solution: return None, 0

    total_time_all_vehicles = 0

    for vehicle_id in range(vehicle_count):
        v_obj = vehicles[vehicle_id]
        v_obj.route = []
        v_obj.filling = 0

        index = routing.Start(vehicle_id)
        current_v_time_s = 0.0

        while True:
            node_idx = manager.IndexToNode(index)
            node = nodes[node_idx]
            v_obj.route.append(node)
            v_obj.filling += node.demand

            if routing.IsEnd(index): break

            # Pobieramy następny krok
            next_index = solution.Value(routing.NextVar(index))
            next_node_idx = manager.IndexToNode(next_index)
            next_node = nodes[next_node_idx]

            # --- TO SAMO CO W ACO ---
            current_v_time_s += distance_matrix[node_idx][next_node_idx]

            if next_node_idx != 0:
                if current_v_time_s > next_node.time_window_s[1]:
                    current_v_time_s += next_node.penalty_s[1]
                elif current_v_time_s < next_node.time_window_s[0]:
                    current_v_time_s = next_node.time_window_s[0]
                current_v_time_s += next_node.service_s

            index = next_index

        total_time_all_vehicles += current_v_time_s

    # Zwracamy sumę w minutach, żeby pasowało do printa
    return vehicles, total_time_all_vehicles