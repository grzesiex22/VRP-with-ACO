import sys

import VRP3.Problem.VRP


def greedy_vrp(nodes, problem: VRP3.Problem.VRP.VRP):

    def get_cost(next_node, vehicle):
        current_node = vehicle.route[-1]
        travel = problem.time_matrix_seconds[current_node.id][next_node.id]
        arrival = vehicle.duration + travel

        # Jeśli wracamy do bazy (id=0), nie liczymy czekania ani kar
        if next_node.id == 0:
            return travel

        wait = max(next_node.time_window_s[0] - arrival, 0)
        penalty = next_node.penalty_s[1] if arrival > next_node.time_window_s[1] else 0
        return travel + wait + penalty + next_node.service_s

    def get_next_node(nodes, vehicle):
        min_cost = sys.maxsize
        best_node = None
        for node in nodes:
            if vehicle.filling + node.demand > vehicle.capacity:
                continue
            cost = get_cost(node, vehicle)
            if cost < min_cost:
                min_cost = cost
                best_node = node
        return best_node, min_cost

    unvisited = nodes[1:]
    total_cost = 0

    for vehicle in problem.vehicles:
        vehicle.route.append(nodes[0])

        while len(unvisited) > 0:
            next_node, cost = get_next_node(unvisited, vehicle)
            if next_node is None:
                break
            vehicle.route.append(next_node)
            vehicle.duration += cost
            vehicle.filling += next_node.demand
            unvisited.remove(next_node)

        vehicle.duration += get_cost(nodes[0], vehicle)
        total_cost += vehicle.duration
        vehicle.route.append(nodes[0])

    return problem, total_cost
