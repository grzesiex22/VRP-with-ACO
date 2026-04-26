import matplotlib.pyplot as plt


class Visualizer:

    def __init__(self, nodes):
        self.nodes = nodes
        self.title = "Tytuł"
        # lista kolorów dla pojazdów
        self.colors = [
            "red", "blue", "green", "orange", "purple",
            "brown", "pink", "gray", "olive", "cyan"
        ]
        # Inicjalizujemy atrybuty, które wypełni metoda create()
        self.fig = None
        self.ax = None

        plt.ioff()

    def create(self, title="VRP Visualization"):
        """Przygotowuje czyste płótno i rysuje punkty bazowe."""
        # Używamy subplots, aby mieć jawny dostęp do obiektu Figure i Axes
        if self.fig:
            plt.close(self.fig)

        self.title = title
        self.fig, self.ax = plt.subplots(figsize=(10, 10))

        self._draw_nodes()

        self.ax.set_title(self.title)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.grid(True, linestyle='--', alpha=0.6)

    def _draw_nodes(self):

        x = [node.x for node in self.nodes]
        y = [node.y for node in self.nodes]

        # depot
        plt.scatter(self.nodes[0].x, self.nodes[0].y, s=150, marker="s", color="black")

        # klienci
        plt.scatter(x[1:], y[1:], color="black")

        for node in self.nodes:
            # Formatowanie czasu HH:MM:SS
            t0_str = node.time_window[0].strftime("%H:%M")
            t1_str = node.time_window[1].strftime("%H:%M")

            # Logika wyświetlania etykiety
            if node.id == 0:
                label = f"DEPOT\n[{t0_str}-{t1_str}]"
            else:
                label = f"ID:{node.id} D:{node.demand}\n[{t0_str}-{t1_str}]"

            self.ax.text(node.x, node.y + 1, label, fontsize=8, ha='center', va='bottom')

    def add_routes(self, vehicles):
        """Dorysowuje trasy do istniejącego wykresu."""
        if self.ax is None:
            self.create()

        for i, v in enumerate(vehicles):
            if len(v.route) < 2: continue

            color = self.colors[i % len(self.colors)]
            route = v.route

            # Rysowanie linii i strzałek
            for j in range(len(route) - 1):
                a, b = route[j], route[j + 1]

                # Główna linia
                self.ax.plot([a.x, b.x], [a.y, b.y], color=color, linewidth=1.5, alpha=0.7, zorder=2)

                # Strzałka kierunkowa
                self.ax.annotate('', xy=(b.x, b.y), xytext=(a.x, a.y),
                                 arrowprops=dict(arrowstyle='->', color=color, lw=1, alpha=0.6),
                                 zorder=3)

    def show(self, block=True):
        """Wyświetla okno."""
        if self.fig:
            self.fig.show() if not block else plt.show()

    def save(self, fname):
        """Zapisuje aktualny stan figury do pliku."""
        if self.fig:
            self.fig.savefig(fname, bbox_inches='tight')
            print(f"Wykres zapisany: {fname}")
        else:
            print(f"Brak wykresu")

    def clear_routes(self):
        """Czyści tylko linie tras, zostawiając węzły (przydatne do animacji)."""
        # Usuwamy wszystkie linie i annotacje z osi
        for line in self.ax.get_lines():
            line.remove()
        for art in self.ax.get_children():
            if isinstance(art, plt.Annotation):
                art.remove()
        # Ponownie rysujemy węzły, bo get_lines mogło usunąć coś za dużo
        self._draw_nodes()
