import json
from colorama import Fore, Style
class Helpers:
    @staticmethod
    def save_json(_file_path, data_to_serialize, verbose=True):
        '''
        Zapisuje jsona w wybranym pliku
        '''
        file_path = _file_path if _file_path.endswith(".json") else f"{_file_path}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_to_serialize, f, indent=4, default=str)
            if verbose:
                print(f"{Fore.GREEN}[VRP_Saver]{Style.RESET_ALL} Dane zapisane w: {Fore.CYAN}{file_path}")
        except Exception as e:
            print(f"{Fore.RED}[VRP_Saver] BŁĄD: {e}{Style.RESET_ALL}")

    @staticmethod
    def convert(obj):
        '''
        Zamienia wszystkie możliwe stringi na liczby w listach i słownikach
        '''
        if isinstance(obj, dict):
            return {k: Helpers.convert(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [Helpers.convert(x) for x in obj]

        if isinstance(obj, str):
            try:
                return float(obj)
            except ValueError:
                return obj

        return obj
