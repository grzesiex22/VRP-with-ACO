import itertools
import csv
import time
import os
from datetime import datetime

from tqdm import tqdm

from VRP3.Problem.Vehicle import Vehicle
from VRP3.Utills.VRP_saver import VRP_saver


class ResearchRunner:
    def __init__(self, solver_info, folder_name=None, subfolder_name=None):
        """
        Inicjalizacja na podstawie słownika konfiguracyjnego solvera.
        Oczekuje słownika z kluczami: 'save_name', 'class' oraz 'params'.
        """
        self.solver_info = solver_info
        self.solver_name = solver_info.get("name", "Unknown ACO")
        self.save_name = solver_info.get("save_name", "ACO")
        self.solver_class = solver_info["class"]
        self.default_params = solver_info.get("params", {}).copy()


        # Globalne zmienne do śledzenia rekordów
        self.global_best_score = float('inf')
        self.global_best_config_str = "None"
        self.global_best_vehicles = None
        self.global_best_history = None

        self.folder_name = folder_name
        self.subfolder_name = subfolder_name
        self.path_csv = None
        self.file_name_best_run_history = None
        self.file_name_best_run = None
        self.results_dir = VRP_saver.set_folder(self.folder_name, self.subfolder_name)

    @staticmethod
    def _format_cfg_str(cfg):
        """Pomocnicza funkcja formatująca parametry do krótkiego stringa na pasku postępu."""
        return (f"α:{cfg['alpha']}|β:{cfg['beta']}|E:{cfg['evaporation']}|P:{cfg['patience']}"
                f"|PBS:{cfg['patience_big_shake']}|IBS:{cfg['intensity_big_shake']}")

    def _load_global_best(self):
        """Skanuje plik wynikowy w poszukiwaniu dotychczasowego rekordu."""
        if not os.path.exists(self.path_csv):
            return

        try:
            with open(self.path_csv, 'r', newline='') as f:
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

    def _load_best_files(self, problem_nodes):
        """Wczytuje fizyczne pliki najlepszego rozwiązania i historii do pamięci."""
        import json

        # Przygotowujemy mapę ID -> Obiekt Node, żeby szybko budować trasę
        nodes_dict = {node.id: node for node in problem_nodes}

        # Ścieżki do plików JSON
        path_history = os.path.join(self.results_dir, self.file_name_best_run_history)
        path_best_run = os.path.join(self.results_dir, self.file_name_best_run)

        # Wczytywanie historii
        if os.path.exists(path_history):
            try:
                with open(path_history, 'r', encoding='utf-8') as f:
                    self.global_best_history = json.load(f)
            except Exception as e:
                print(f"Błąd wczytywania historii: {e}")

        # Wczytywanie pojazdów (Best Run)
        if os.path.exists(path_best_run):
            try:
                with open(path_best_run, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.global_best_score = data.get('cost_minutes', self.global_best_score)

                    # Konwersja listy słowników na listę obiektów Vehicle
                    self.global_best_vehicles = []
                    for v_data in data.get('vehicles', []):
                        vehicle_obj = Vehicle.from_dict(v_data, nodes_dict)
                        self.global_best_vehicles.append(vehicle_obj)

                print(f"Pomyślnie wczytano rekordowe pojazdy (Koszt: {self.global_best_score:.2f})")
            except Exception as e:
                print(f"Błąd wczytywania best_run.json: {e}")

    def _get_completed_tasks(self):
        """Pobiera zbiór par (config_id, repeat), które są już w pliku."""
        completed = set()
        if not os.path.exists(self.path_csv):
            return completed

        try:
            with open(self.path_csv, 'r', newline='') as f:
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
        best_history = None

        # 1. Dynamiczna nazwa pliku na podstawie słownika i problemu
        liczba_miast = len(problem.nodes) - 1  # Zakładamy, że 1 węzeł to Depot
        liczba_mrowek = self.default_params.get("ants", 0)

        ext = f"research_dataset_{self.save_name}_C{liczba_miast}_A{liczba_mrowek}_R{repeats}"
        file_name_csv = f"{ext}.csv"
        self.path_csv = os.path.join(self.results_dir, file_name_csv)
        self.file_name_best_run_history = f"{ext}_history.json"
        self.file_name_best_run = f"{ext}_best_run.json"

        # 2. Konfiguracje i WCZYTYWANIE
        configs = self.generate_configs()
        completed_tasks = self._get_completed_tasks()

        # Najpierw koszt z CSV, potem pliki binarne/json
        self._load_global_best()
        self._load_best_files(problem_nodes=problem.nodes)

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
            file_exists = os.path.isfile(self.path_csv)
            with open(self.path_csv, 'a', newline='') as f:
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
                    best_vehicles, best_cost, best_history = solver.run()

                    elapsed = time.time() - start

                    # Aktualizacja globalnego rekordu, jeśli mrówki pobiły czas
                    if best_cost < self.global_best_score:
                        self.global_best_score = best_cost
                        self.global_best_config_str = current_cfg_str
                        self.global_best_vehicles = best_vehicles
                        self.global_best_history = best_history

                        VRP_saver.save_aco(
                            aco_cfg=self.solver_info,
                            vehicles=best_vehicles,
                            cost=best_cost,
                            folder_name=self.results_dir,
                            file_name=self.file_name_best_run,
                            verbose=False
                        )

                        VRP_saver.save_history(
                            history=best_history,
                            folder_name=self.results_dir,
                            file_name=self.file_name_best_run_history,
                            verbose=False
                        )

                    # Wyciągamy ostatnie wartości z list historii
                    history_avg = best_history['avg']
                    last_avg = history_avg[-1] / 60 if history_avg else None

                    # Wyciągamy informację o ostatnim Shake'u (jeśli lista nie jest pusta)
                    big_shake_list = best_history.get('big_shakes_iters', [])
                    last_shake_iter = big_shake_list[-1] if big_shake_list else -1

                    # Zapisujemy WSZYSTKIE kolumny
                    row = {
                        "config_id": idx,
                        "repeat": r,
                        "best_cost_minutes": round(best_cost / 60, 4),
                        "best_iteration": best_history.get("best_iter_nr", -1),
                        "avg_cost_final_minutes": round(last_avg, 4) if last_avg else None,
                        "diversity_final": round(best_history.get("diversity_final", -1), 4),
                        "iterations_done": best_history.get("iters_done", -1),
                        "execution_time": round(elapsed, 2),
                        "big_shakes_count": best_history.get("big_shakes_count", 0),
                        "big_shakes_at_iter": big_shake_list,
                        "last_big_shake_iter": last_shake_iter
                    }
                    row.update(cfg)  # Dodaje wszystkie parametry z cfg do wiersza

                    writer.writerow(row)
                    f.flush()
                    pbar.update(1)

        print(f"\nGotowe! Najlepszy czas: {self.global_best_score:.2f} min (Konfiguracja: {self.global_best_config_str})")
        print(f"Wyniki zapisano w: {self.path_csv}")

        return self.global_best_vehicles, self.global_best_score, self.global_best_history
