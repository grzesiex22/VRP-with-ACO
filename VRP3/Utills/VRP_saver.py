import json
import os
from colorama import Fore, Style
from VRP3.Problem.VRP import VRP
from VRP3.Utills.Generator import Generator
from copy import deepcopy

class VRP_saver:

    @staticmethod
    def set_path(folder_name="Results",  dataset_name="Dataset_05", extension="_problem_def.json"):
        # 1. DYNAMICZNE USTALANIE ŚCIEŻKI
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base_dir_results = os.path.join(base_dir, folder_name)

        # Budujemy ścieżkę do podfolderu dataset
        target_dir = os.path.join(base_dir_results, dataset_name)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, f"{dataset_name.lower()}{extension.lower()}")

        return file_path
    
    @staticmethod
    def save_json(file_path, data_to_serialize, mode='w'):
        try:
            with open(file_path, mode, encoding="utf-8") as f:
                json.dump(data_to_serialize, f, indent=4, default=str)
            print(f"{Fore.GREEN}[VRP_Saver]{Style.RESET_ALL} Dane zapisane w: {Fore.CYAN}{file_path}")
        except Exception as e:
            print(f"{Fore.RED}[VRP_Saver] BŁĄD: {e}{Style.RESET_ALL}")

    
    @staticmethod
    def save_problem(vrp_problem: VRP, generator_obj: Generator, folder_name="Results",  dataset_name="Dataset_05"):
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

        file_path = VRP_saver.set_path(folder_name, dataset_name, extension="_problem_def.json")
        VRP_saver.save_json(file_path, data_to_serialize)


    @staticmethod
    def save_aco_configs(aco_cfgs, folder_name="Results",  dataset_name="Dataset_05"):
        """
        Zapisuje konfiguracje algorytmów.
        """

        data_to_serialize = deepcopy(aco_cfgs)

        for cfg in data_to_serialize:
            cfg["class"] = cfg["class"].__name__
        
        file_path = VRP_saver.set_path(folder_name, dataset_name, extension="_aco_cfgs.json")
        VRP_saver.save_json(file_path, data_to_serialize)


    def save_aco(aco_cfg, vehicles, cost,  folder_name="Results",  dataset_name="Dataset_05", extension="_aco_1.json"):
        """
        Zapisuje konfiguracje algorytmu, koszt trasy i trasy pojazdów.
        """
        # konfiguracja
        data_to_serialize = dict()

        cfg = deepcopy(aco_cfg)
        cfg["class"] = cfg["class"].__name__

        data_to_serialize["cfg"] = cfg

        # koszt trasy
        data_to_serialize["cost"] = cost

        # pojazdy/trasy
        vehicles_json = []
        for i, v in enumerate(vehicles):
            vehicles_json.append(v.to_json())

        data_to_serialize['vehicles'] = vehicles_json
        
        # Zapis
        file_path = VRP_saver.set_path(folder_name, dataset_name, extension=extension)
        VRP_saver.save_json(file_path, data_to_serialize)

    def save_solution(vehicles, cost,  folder_name="Results",  dataset_name="Dataset_05", extension="_greedy.json"):
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
        file_path = VRP_saver.set_path(folder_name, dataset_name, extension=extension)
        VRP_saver.save_json(file_path, data_to_serialize)

    

    



