import matplotlib.pyplot as plt


class Visualizer:

    def __init__(self, nodes):
        self.nodes = nodes

    def draw_nodes(self):

        x = [node.x for node in self.nodes]
        y = [node.y for node in self.nodes]

        # depot
        plt.scatter(self.nodes[0].x, self.nodes[0].y, s=150, marker="s")

        # klienci
        plt.scatter(x[1:], y[1:])

        # podpisy
        for node in self.nodes:
            plt.text(node.x, node.y, str(node.id))

    def draw_route(self, route):

        for i in range(len(route) - 1):

            a = self.nodes[route[i]]
            b = self.nodes[route[i + 1]]

            plt.plot([a.x, b.x], [a.y, b.y])

    def show(self, route):

        plt.figure(figsize=(8, 8))

        self.draw_nodes()
        self.draw_route(route)

        plt.title("Vehicle Routing Problem - best route")
        plt.xlabel("X")
        plt.ylabel("Y")

        plt.grid(True)
        plt.show()