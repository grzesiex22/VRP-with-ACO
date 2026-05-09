

class Vehicle:
    def __init__(self, id, capacity, filling=0):
        self.id = id
        self.route = []
        self.capacity = capacity
        self.filling = filling
        self.duration = 0

    def __copy__(self):
        return Vehicle(self.id, self.capacity, self.filling)

    def __repr__(self):
        return f"Vehicle(id={self.id}, capacity={self.capacity})"

    def to_json(self):
        route_str = []
        for r in self.route:
            route_str.append(f"{r.id}")
        route_str = "->".join(route_str)

        return {
            "id": self.id,
            "route": route_str,
            "capacity": self.capacity,
            "filling": self.filling,
            "duration": self.duration
        }

    @staticmethod
    def from_dict(data, nodes_dict):
        """
        Tworzy obiekt Vehicle na podstawie słownika z JSON.
        nodes_dict: słownik {id_węzła: obiekt_Node}
        """
        # Tworzymy nową instancję pojazdu
        v = Vehicle(id=data['id'], capacity=data['capacity'], filling=data['filling'])
        v.duration = data.get('duration', 0)

        # Rekonstrukcja trasy ze stringa "0->18->2->..." na listę obiektów Node
        route_ids = data['route'].split("->")
        for n_id in route_ids:
            node_obj = nodes_dict.get(int(n_id))
            if node_obj:
                v.route.append(node_obj)

        return v