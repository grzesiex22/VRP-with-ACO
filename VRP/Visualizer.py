import matplotlib.pyplot as plt


class Visualizer:

    def __init__(self, nodes):
        self.nodes = nodes

        # lista kolorów dla pojazdów
        self.colors = [
            "red", "blue", "green", "orange", "purple",
            "brown", "pink", "gray", "olive", "cyan"
        ]

    def draw_nodes(self):

        x = [node.x for node in self.nodes]
        y = [node.y for node in self.nodes]

        # depot
        plt.scatter(self.nodes[0].x, self.nodes[0].y, s=150, marker="s", color="black")

        # klienci
        plt.scatter(x[1:], y[1:], color="black")

        for node in self.nodes:
            plt.text(node.x, node.y, f"{node.id} ({node.demand})")

    def draw_routes(self, routes):

        for i, route in enumerate(routes):
            color = self.colors[i % len(self.colors)]
            self.draw_route(route, color)

    def draw_route(self, route, color):

        for i in range(len(route) - 1):

            a = self.nodes[route[i]]
            b = self.nodes[route[i + 1]]

            plt.plot([a.x, b.x], [a.y, b.y], color=color, linewidth=2)

    def show(self, routes, title=""):

        plt.figure(figsize=(8, 8))

        self.draw_nodes()
        self.draw_routes(routes)

        plt.title(f"{title} - VRP - best routes")
        plt.xlabel("X")
        plt.ylabel("Y")

        plt.grid(True)
        plt.show(block=False)