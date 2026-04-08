

class Vehicle:
    def __init__(self, id, capacity):
        self.id = id
        self.route = []
        self.capacity = capacity
        self.filling = 0
        self.routes = []
        self.duration = 0

    def __copy__(self):
        return Vehicle(self.id, self.capacity)

    def __repr__(self):
        return f"Vehicle(id={self.id}, capacity={self.capacity})"
