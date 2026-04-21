

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
