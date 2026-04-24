import itertools
import csv
import time
import os
from datetime import datetime

from tqdm import tqdm


class ResearchRunner:
    def __init__(self, solver_info, file_path=None):
        """
        Inicjalizacja na podstawie słownika konfiguracyjnego solvera.
        Oczekuje słownika z kluczami: 'save_name', 'class' oraz 'params'.
        """
        self.solver_name = solver_info.get("name", "Unknown ACO")
        self.save_name = solver_info.get("save_name", "ACO")
        self.solver_class = solver_info["class"]
        self.default_params = solver_info.get("params", {}).copy()

        # Globalne zmienne do śledzenia rekordów
        self.global_best_score = float('inf')
        self.global_best_config_str = "None"
        self.results_dir = file_path
        self.results_path = None

    @staticmethod
    def _format_cfg_str(cfg):
        """Pomocnicza funkcja formatująca parametry do krótkiego stringa na pasku postępu."""
        return (f"α:{cfg['alpha']}|β:{cfg['beta']}|E:{cfg['evaporation']}|P:{cfg['patience']}"
                f"|PBS:{cfg['patience_big_shake']}|IBS:{cfg['intensity_big_shake']}")

    def _load_global_best(self):
        """Skanuje plik wynikowy w poszukiwaniu dotychczasowego rekordu."""
        if not os.path.exists(self.results_path):
            return

        try:
            with open(self.results_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cost = float(row['best_cost_minutes'])
                    if cost < self.global_best_score:
                        self.global_best_score = cost
                        # Odtwarzamy string konfiguracyjny do wyświetlania
                        self.global_best_config_str = (
                            f"α:{row['alpha']}|β:{row['beta']}|E:{row['evaporation']}"
                            f"|P:{row['patience']}|PBS:{row['patience_big_shake']}"
                        )
        except (KeyError, ValueError, csv.Error):
            pass

    def _get_completed_tasks(self):
        """Pobiera zbiór par (config_id, repeat), które są już w pliku."""
        completed = set()
        if not os.path.exists(self.results_path):
            return completed

        try:
            with open(self.results_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Zapisujemy jako krotkę (int, int)
                    completed.add((int(row['config_id']), int(row['repeat'])))
        except (KeyError, ValueError, csv.Error):
            pass
        return completed

    def generate_configs(self):
        """Generuje listę unikalnych konfiguracji z filtrowaniem redundancji."""
        # alphas = [0.5]
        # betas = [2.0, 3.5]
        # evaps = [0.05]
        # pats = [100]
        # pb_shakes = [150]
        # intensities = [0.3]

        alphas = [0.5, 1.0, 1.5]
        betas = [2.0, 3.5, 5.0]
        evaps = [0.05, 0.1, 0.2]
        pats = [300, 650, 1000]
        pb_shakes = [100, 250, 400, 999999]
        intensities = [0.3, 0.6]

        configs = []
        for a, b, e, p, pbs, intensity in itertools.product(alphas, betas, evaps, pats, pb_shakes, intensities):
            # Filtr 1: Jeśli shake wyłączony (PBS=999999) lub nieaktywny (PBS >= Patience)
            if pbs >= p or pbs == 999999:
                if intensity == 0.6:  # bierzemy tylko jedną wersję intensity
                    continue

            # Filtr 2: Jeśli patience =< shake_patience i to nie jest przypadek pomijalny to pomiń, bo nie ma sensu
            if pbs >= p and pbs != 999999:
                continue

            # Tworzymy kopię bazy i nadpisujemy zmienne
            cfg = self.default_params.copy()
            cfg.update({
                "alpha": a,
                "beta": b,
                "evaporation": e,
                "patience": p,
                "patience_big_shake": pbs,
                "intensity_big_shake": intensity,
                "big_shake_duration": int(0.2 * pbs) if pbs < p else 0
            })
            configs.append(cfg)

        return configs

    def run_experiment(self, problem, repeats=3):
        """Główna pętla badań."""
        best_cost = 0.0
        best_vehicles = []
        history = None

        # 1. Dynamiczna nazwa pliku na podstawie słownika i problemu
        liczba_miast = len(problem.nodes) - 1  # Zakładamy, że 1 węzeł to Depot
        liczba_mrowek = self.default_params.get("ants", 0)

        ext = f"research_dataset_{self.save_name}_C{liczba_miast}_A{liczba_mrowek}_R{repeats}.csv"
        self.results_path = os.path.join(self.results_dir, ext)

        # 2. Konfiguracje
        configs = self.generate_configs()
        completed_tasks = self._get_completed_tasks()
        self._load_global_best()

        # Przygotowanie nagłówków (wszystkie parametry + wyniki)
        sample_cfg = configs[0]
        param_headers = list(sample_cfg.keys())
        metric_headers = ["config_id", "repeat", "best_cost_minutes", "best_iteration",
                          "avg_cost_final_minutes", "diversity_final",
                          "iterations_done", "execution_time",
                          "big_shakes_count", "big_shakes_at_iter", "last_big_shake_iter"]
        headers = metric_headers + param_headers

        total_tests = len(configs) * repeats
        already_done_count = len(completed_tasks)

        if already_done_count >= total_tests:
            print(f"Wszystkie testy ({total_tests}) są już w pliku!")
            return

        print(f"Wznawianie: Pominięto {already_done_count} wykonanych rekordów. "
              f"Pozostało: {total_tests - already_done_count}")

        # Przygotowanie listy pozostałych zadań
        todo = [(idx, cfg, r) for idx, cfg in enumerate(configs, 1)
                for r in range(1, repeats + 1)
                if (idx, r) not in completed_tasks]

        # 3. Główna pętla z paskiem postępu tqdm
        # unit_scale=False i dynamiczne ncols pozwalają ładnie dopasować pasek do okna terminala
        with tqdm(total=total_tests, desc=f"Badania {self.save_name}", unit="test",
                  dynamic_ncols=True, initial=already_done_count) as pbar:
            file_exists = os.path.isfile(self.results_path)
            with open(self.results_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                if not file_exists:
                    writer.writeheader()

                for idx, cfg, r in todo:
                    current_cfg_str = self._format_cfg_str(cfg)

                    # Aktualizacja paska - co aktualnie liczy i jaki jest najlepszy historycznie setup
                    pbar.set_postfix({
                        "Cfg": f"{idx}/{len(configs)}",
                        "Rep": r,
                        "CurrCfg": current_cfg_str,
                        "BestScore": f"{self.global_best_score:.2f} min",
                        "BestCfg": self.global_best_config_str
                    })

                    start = time.time()

                    # Wywołanie solvera (dynamiczna klasa ze słownika)
                    solver = self.solver_class(
                        problem.copy(),
                        **cfg,
                        verbose=False
                    )
                    best_vehicles, best_cost, history = solver.run()

                    elapsed = time.time() - start

                    best_cost /= 60

                    # Aktualizacja globalnego rekordu, jeśli mrówki pobiły czas
                    if best_cost < self.global_best_score:
                        self.global_best_score = best_cost
                        self.global_best_config_str = current_cfg_str

                    # Wyciągamy ostatnie wartości z list historii
                    history_avg = history['avg']
                    last_avg = history_avg[-1] / 60 if history_avg else None

                    # Wyciągamy informację o ostatnim Shake'u (jeśli lista nie jest pusta)
                    big_shake_list = history.get('big_shakes_iters', [])
                    last_shake_iter = big_shake_list[-1] if big_shake_list else -1

                    # Zapisujemy WSZYSTKIE kolumny
                    row = {
                        "config_id": idx,
                        "repeat": r,
                        "best_cost_minutes": round(best_cost, 4),
                        "best_iteration": history.get("best_iter_nr", -1),
                        "avg_cost_final_minutes": round(last_avg, 4) if last_avg else None,
                        "diversity_final": round(history.get("diversity_final", -1), 4),
                        "iterations_done": history.get("iters_done", -1),
                        "execution_time": round(elapsed, 2),
                        "big_shakes_count": history.get("big_shakes_count", 0),
                        "big_shakes_at_iter": big_shake_list,
                        "last_big_shake_iter": last_shake_iter
                    }
                    row.update(cfg)  # Dodaje wszystkie parametry z cfg do wiersza

                    writer.writerow(row)
                    f.flush()
                    pbar.update(1)

        print(f"\nGotowe! Najlepszy czas: {self.global_best_score:.2f} min (Konfiguracja: {self.global_best_config_str})")
        print(f"Wyniki zapisano w: {self.results_path}")

        return best_vehicles, best_cost, history
