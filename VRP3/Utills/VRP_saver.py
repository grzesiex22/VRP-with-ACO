import json
import os
from colorama import Fore, Style
from VRP3.Problem.VRP import VRP
from VRP3.Utills.Generator import Generator
from copy import deepcopy


class VRP_saver:

    @staticmethod
    def set_path(folder_name, file_name, subfolder_name=None):
        # Budujemy ścieżkę do podfolderu dataset
        target_dir = VRP_saver.set_folder(folder_name=folder_name, subfolder_name=subfolder_name)
        file_path = os.path.join(target_dir, file_name)

        return file_path

    @staticmethod
    def set_folder(folder_name="Results", subfolder_name=None):
        # 1. DYNAMICZNE USTALANIE ŚCIEŻKI BAZOWEJ
        # Ścieżka do katalogu głównego projektu
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # 2. BUDOWANIE ŚCIEŻKI DO TARGETU
        # Sprawdzamy, czy subfolder_name został podany
        if subfolder_name:
            # Struktura: base/Results/Moje_Badania/Dataset_05
            target_dir = os.path.join(base_dir, folder_name, subfolder_name)
        else:
            # Struktura standardowa: base/Results/Dataset_05
            target_dir = os.path.join(base_dir, folder_name)

        # 3. TWORZENIE FOLDERU (jeśli nie istnieje)
        # exist_ok=True zapobiega błędom, gdy procesy próbują stworzyć folder jednocześnie
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # 4. ZWRACANIE ŚCIEŻKI DO FOLDERU
        return target_dir

    @staticmethod
    def save_json(_file_path, data_to_serialize, verbose=True):
        file_path = _file_path if _file_path.endswith(".json") else f"{_file_path}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_serialize, f, indent=4, default=str)
            if verbose:
                print(f"{Fore.GREEN}[VRP_Saver]{Style.RESET_ALL} Dane zapisane w: {Fore.CYAN}{file_path}")
        except Exception as e:
            print(f"{Fore.RED}[VRP_Saver] BŁĄD: {e}{Style.RESET_ALL}")

    @staticmethod
    def save_problem(vrp_problem: VRP, generator_obj: Generator, folder_name="Results",
                     dataset_name="Dataset_05", file_name=None,
                     subfolder_name=None, verbose=True):
        """
        Zapisuje parametry generatora oraz pełną definicję problemu VRP do pliku JSON.
        """

        # 2. PRZYGOTOWANIE DANYCH (tak jak wcześniej)
        data_to_serialize = {
            "metadata": {
                "dataset": dataset_name,
                "num_nodes": len(vrp_problem.nodes),
                "num_vehicles": len(vrp_problem.vehicles)
            },
            "generator_params": vars(generator_obj),  # Szybki trik: vars() wyciąga wszystkie atrybuty obiektu
            "nodes": [
                {
                    "id": n.id, "x": n.x, "y": n.y, "demand": n.demand,
                    "service": n.service, "time_window": n.time_window, "penalty": n.penalty
                } for n in vrp_problem.nodes
            ],
            "vehicles": [
                {"id": v.id, "capacity": v.capacity} for v in vrp_problem.vehicles
            ]
        }

        # Zapis
        target_dir = VRP_saver.set_folder(folder_name, subfolder_name=subfolder_name)
        if file_name is None:
            file_name = f"{dataset_name}_problem_def.json"
        file_path = os.path.join(target_dir, file_name)
        VRP_saver.save_json(file_path, data_to_serialize, verbose=verbose)

    @staticmethod
    def save_aco(aco_cfg, vehicles, cost, folder_name, file_name, subfolder_name=None, verbose=True):
        """
        Zapisuje konfiguracje algorytmu, koszt trasy i trasy pojazdów.
        """
        # konfiguracja
        data_to_serialize = dict()

        cfg = deepcopy(aco_cfg)
        # Obsługa przypadku, gdy "class" to obiekt klasy lub string
        if "class" in cfg and not isinstance(cfg["class"], str):
            cfg["class"] = cfg["class"].__name__

        data_to_serialize["cfg"] = cfg
        data_to_serialize["cost"] = cost
        data_to_serialize["cost_minutes"] = cost / 60
        data_to_serialize["vehicles"] = [v.to_json() for v in vehicles]

        # 2. Budowanie ścieżki z uwzględnieniem subfolderu
        # folder_name (np. "Research") -> subfolder_name (np. "ACO_Tests") -> dataset_name (np. "C40")
        target_dir = VRP_saver.set_folder(folder_name, subfolder_name=subfolder_name)
        file_path = os.path.join(target_dir, file_name)

        # 3. Zapis
        VRP_saver.save_json(file_path, data_to_serialize, verbose=verbose)

    @staticmethod
    def save_history(history, folder_name, file_name, subfolder_name=None, verbose=True):
        """
        Zapisuje słownik historii (listy kosztów, diversity itp.) do pliku JSON.
        """
        # Upewniamy się, że folder istnieje (korzystając z Twojej metody set_folder)
        target_dir = VRP_saver.set_folder(folder_name, subfolder_name=subfolder_name)

        # Przygotowujemy pełną ścieżkę (zamieniamy .csv na .json jeśli trzeba)
        file_name = file_name if file_name.endswith(".json") else f"{file_name}.json"
        save_path = os.path.join(target_dir, file_name)

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                # indent=4 sprawi, że plik będzie czytelny dla człowieka
                json.dump(history, f, indent=4, ensure_ascii=False)
            # print(f"Historia zapisana poprawnie: {save_path}")
        except Exception as e:
            print(f"Błąd podczas zapisu historii: {e}")

    @staticmethod
    def save_solution(vehicles, cost, folder_name, file_name, subfolder_name=None, verbose=True):
        """
        Zapisuje koszt trasy i trasy pojazdów.
        """
        # konfiguracja
        data_to_serialize = dict()

        # koszt trasy
        data_to_serialize["cost"] = cost

        # pojazdy/trasy
        vehicles_json = []
        for i, v in enumerate(vehicles):
            vehicles_json.append(v.to_json())

        data_to_serialize['vehicles'] = vehicles_json

        # Zapis
        target_dir = VRP_saver.set_folder(folder_name, subfolder_name=subfolder_name)
        file_path = os.path.join(target_dir, file_name)
        VRP_saver.save_json(file_path, data_to_serialize, verbose=verbose)

