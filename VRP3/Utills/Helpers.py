import json
from colorama import Fore, Style
class Helpers:
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
