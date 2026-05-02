from VRP3.ACO_for_VRP_3 import ACO_for_VRP_3
from VRP3.ACO_for_VRP_4 import ACO_for_VRP_4
from VRP3.Utills.Generator import Generator
from VRP3.Utills.Visualizer import Visualizer, plt

import itertools
import csv
import time
import os
import time

from tqdm import tqdm

from VRP3.Problem.Vehicle import Vehicle
from VRP3.Utills.VRP_saver import VRP_saver
from VRP3.Problem.VRP import VRP


class Tester:
    def __init__(self):
        self.dataset_configs = self.generate_dataset()
        self.path_csv = None
        self.save_name = None

    def generate_dataset(self):
        seeds = [50, 51, 52, 53]
        nodes = [20, 40, 60, 80]
        capacity_scalers = [1.3, 1.6, 2.0]
        time_windows = [5, 10, 15, 20] 

        # seeds = [50, 51]
        # nodes = [10, 20]
        # capacity_scalers = [1.3, 1.5]
        # time_windows = [5, 10] 

        dataset_configs = []

        id = 0
        for s in seeds:
            for n in nodes:
                for t in time_windows:
                    for cs in capacity_scalers:
                        dataset_configs.append({
                            "id": id,
                            "ants": n,
                            "n": n,
                            "t1": t,
                            "cs": cs,
                            "seed": s
                        })
                        id += 1

        return dataset_configs
    
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


    def run(self, path_csv, aco_config, repeats=10):
        print('%'*100)
        print(f'--- TESTY NA ZESTAWACH DANYCH ROZPOCZĘTO ---')
        print(f'--- Wersja ACO: {aco_config['name']}')
        print(f'--- Zapisywanie do: {path_csv}')
        print('%'*100)

        # Dane zapisu do pliku
        self.path_csv = path_csv
        self.save_name = path_csv.rsplit('/', maxsplit=1)[1]

        # Wczytanie postępu (ustalenie liczby iteracji)        
        total_tests = len(self.dataset_configs) * repeats
        completed_tasks = self._get_completed_tasks()
        already_done_count = len(completed_tasks)

        if already_done_count >= total_tests:
            print(f"Wszystkie testy ({total_tests}) są już w pliku!")
            return

        print(f"Wznawianie: Pominięto {already_done_count} wykonanych rekordów. "
              f"Pozostało: {total_tests - already_done_count}")

        # Przygotowanie listy pozostałych zadań
        todo = [
            (cfg['id'], cfg, r)
            for cfg in self.dataset_configs
            for r in range(1, repeats + 1)
            if (cfg['id'], r) not in completed_tasks
        ]

        need_headers = not os.path.exists(self.path_csv)

        if need_headers:
            VRP_saver.prepare_saving_file(self.path_csv, verbose=True)

        with open(self.path_csv, 'a') as f:
            writer = None

            with tqdm(
                total=total_tests,
                desc=f"Badania {self.save_name}",
                unit="test",
                dynamic_ncols=True,
                initial=already_done_count
            ) as pbar:

                for config_id, config, repeat in todo:

                        # Przygotowanie problemu
                        ants = config["ants"]
                        generator = Generator(
                            n=config["n"],
                            t1=config["t1"],
                            cs=config["cs"],
                            seed=config["seed"]
                        )

                        params = generator.get_parameters()
                        nodes, vehicles = generator.generate()
                        problem = VRP(nodes, vehicles=vehicles)

                        # Przygotowanie instancji ACO
                        if aco_config["params"] is None:
                            print(f"⚠️ W {aco_config['name']} - brak parametrów.")
                            return

                        ACO_Class = aco_config["class"]
                        params = aco_config["params"].copy()
                        params["ants"] = ants
                        params["iterations"] = 10

                        aco_instance = ACO_Class(problem.copy(), **params)
                        aco_instance.verbose = False

                        # Uruchomienie testu i pomiar czasu
                        start = time.perf_counter()

                        vehicles, cost, history = aco_instance.run()

                        end = time.perf_counter()

                        duration = end - start


                        # Zapis danych do csv
                        serialized = {
                            'config_id': config['id'],
                            'repeat': repeat,
                            'cost': cost,
                            'ants': ants,
                            'duration': duration
}
                        serialized.update(generator.get_parameters())
                        serialized['duration'] = end - start

                        if writer is None:
                            writer = csv.DictWriter(f, serialized.keys(), lineterminator='\n')
                            if need_headers:
                                writer.writeheader()

                        writer.writerow(serialized)
                        f.flush()  # opcjonalnie dla bezpieczeństwa

                        pbar.update(1)



                

