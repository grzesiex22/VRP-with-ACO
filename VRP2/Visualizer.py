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
            # Formatowanie czasu HH:MM:SS
            t0_str = node.time_window[0].strftime("%H:%M:%S")
            t1_str = node.time_window[1].strftime("%H:%M:%S")

            plt.text(node.x, node.y, f"ID:{node.id} D:{node.demand}\n [{t0_str}-{t1_str}]")

    def draw_routes(self, routes):

        for i, route in enumerate(routes):
            color = self.colors[i % len(self.colors)]
            self.draw_route(route, color)

    def draw_route(self, route, color):
        # Styl strzałki: bardzo mała, subtelna
        arrow_props = dict(
            arrowstyle='->, head_length=0.3, head_width=0.2',  # Drastyczne zmniejszenie grotu
            color=color,
            linewidth=0.8,  # Cieńsza linia grotu
            alpha=0.6,  # Lekka przezroczystość
            shrinkA=3,  # Przesunięcie startu strzałki od punktu A (zorder)
            shrinkB=3  # Przesunięcie grotu od punktu B (zorder)
        )

        for i in range(len(route) - 1):

            a = route[i]
            b = route[i + 1]

            # 1. Rysujemy główną linię trasy
            plt.plot([a.x, b.x], [a.y, b.y], color=color, linewidth=1.5, alpha=0.7)

            # 2. Rysujemy małą strzałkę
            # plt.annotate nie rysuje linii, tylko dodaje strzałkę między punktami.
            # shrinkA/shrinkB sprawiają, że nie nachodzi ona na kropki klientów.
            plt.annotate('', xy=(b.x, b.y), xytext=(a.x, a.y),
                         arrowprops=arrow_props, zorder=2)

    def show(self, routes, title=""):

        plt.figure(figsize=(8, 8))

        self.draw_nodes()
        self.draw_routes(routes)

        plt.title(f"{title} - VRP - best routes")
        plt.xlabel("X")
        plt.ylabel("Y")

        plt.grid(True)
        plt.show(block=False)