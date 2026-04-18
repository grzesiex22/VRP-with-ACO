import matplotlib.pyplot as plt
import os
from colorama import Fore, Style


class Plotter:
    def __init__(self, folder_name="Results"):
        # Automatyczne wykrywanie folderu, w którym znajduje się uruchomiony skrypt (main.py)
        # i tworzenie w nim podfolderu 'Results'
        self.main_path = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.join(self.main_path, folder_name)

        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)

        plt.ion()

    def plot_single_aco(self, name, history, greedy_baseline=None, save=True, show=True, dataset="Dataset_1"):
        """
        :param name: Nazwa konfiguracji (np. "ACO 1")
        :param history: Słownik z danymi historycznymi
        :param greedy_baseline: Koszt algorytmu Greedy do linii odniesienia
        :param save: Czy zapisać plik na dysku
        :param dataset: Początek nazwy pliku podany przez użytkownika
        """
        plt.figure(figsize=(10, 6))

        # Konwersja danych na minuty
        iterations = range(len(history['overall']))
        best_overall = [c / 60 for c in history['overall']]
        avg_iter = [c / 60 for c in history['avg']]
        iter_best = [c / 60 for c in history['iter_best']]

        # Rysowanie linii
        plt.plot(iterations, best_overall, color='red', linewidth=3, label='Najlepszy wynik (Best Overall)')
        plt.plot(iterations, avg_iter, color='green', alpha=0.7, label='Średni wynik iteracji (Avg Iteration)')
        plt.plot(iterations, iter_best, 'b', alpha=0.7, label='Najlepszy wynik iteracji (Best Iteration)')

        # # Wypełnienie obszaru między najlepszym a średnim (pokazuje zróżnicowanie mrówek)
        # plt.fill_between(iterations, best_overall, avg_iter, color='blue', alpha=0.05)

        # Dodanie linii Greedy jako punktu odniesienia
        if greedy_baseline:
            plt.axhline(y=greedy_baseline / 60, color='black', linestyle='--', alpha=0.6, label='Baseline (Greedy)')

        # Formatowanie wykresu
        plt.title(f"Postęp optymalizacji: {name}", fontsize=14, fontweight='bold')
        plt.xlabel("Iteracja")
        plt.ylabel("Koszt trasy (minuty)")
        plt.legend(loc='upper right')
        plt.grid(True, linestyle=':', alpha=0.6)

        # --- SKALOWANIE OSI Y ---
        if len(best_overall) > 10:
            # Wybieramy dane ACO do skali (pomijamy początkowe piki/kary)
            start_idx = int(len(best_overall) * 0.05)
            aco_relevant = best_overall[start_idx:]

            y_min = min(aco_relevant)
            y_max = max(aco_relevant)

            # Jeśli mamy baseline, musi się on zmieścić w kadrze
            if greedy_baseline:
                g_val = greedy_baseline / 60
                y_min = min(y_min, g_val)
                y_max = max(y_max, g_val)

            # Ustawiamy limity z małym marginesem (2% dół, 5% góra)
            plt.ylim(y_min * 0.95, y_max * 1.2)

        # --- LOGIKA ZAPISU DO PODFOLDERÓW ---
        if save:
            # 1. Tworzymy podfolder dla datasetu (np. Results/Dataset_1)
            dataset_dir = os.path.join(self.base_dir, dataset)
            if not os.path.exists(dataset_dir):
                os.makedirs(dataset_dir, exist_ok=True)

            # 2. Budujemy nazwę pliku: [dataset]_[typ]_[algorytm].png
            # typ: 'conv' jako skrót od convergence (zbieżność)
            clean_aco_name = name.replace(" ", "_").lower()
            filename = f"{dataset.lower()}_conv_{clean_aco_name}.png"
            file_path = os.path.join(dataset_dir, filename)

            plt.savefig(file_path)
            print(f"{Fore.CYAN}Wykres zapisany w: {Style.BRIGHT}{file_path}{Style.RESET_ALL}")

        # Wyświetlanie
        plt.draw()

        if show:
            plt.show(block=False)
        else:
            plt.close()

        # plt.pause(2)

    def plot_comparison_only_best(self, all_histories):
        """
        Opcjonalny, dodatkowy wykres: tylko najlepsze linie wszystkich ACO
        na jednym obrazku dla szybkiego porównania końcowego.
        """
        plt.figure(figsize=(10, 6))
        for name, history in all_histories.items():
            plt.plot([c / 60 for c in history['overall']], label=name)

        plt.title("Porównanie zbieżności najlepszych wyników")
        plt.xlabel("Iteracja")
        plt.ylabel("Koszt (min)")
        plt.legend()
        plt.savefig(os.path.join(self.base_dir, "comparison_all.png"))
        # plt.close()