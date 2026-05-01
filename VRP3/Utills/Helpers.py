import json
import re
from colorama import Fore, Style


class Helpers:
    @staticmethod
    def can_be_tuple(obj: str):
        if re.match(r'^\((\w,)|((\w,)+\w)\)$', obj):
            return True
        return None
    
    @staticmethod
    def str_to_tuple(obj: str):
        obj = obj.strip('(').strip(')').replace(' ', '')
        s_elems = obj.split(',')
        
        tup = tuple(map(Helpers.convert, s_elems))
        return tup

    @staticmethod
    def convert(obj):
        '''
        Zamienia wszystkie możliwe stringi na inty w listach i słownikach
        '''
        if isinstance(obj, dict):
            return {k: Helpers.convert(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [Helpers.convert(x) for x in obj]

        if isinstance(obj, str):
            try:                
                return int(obj)
            except ValueError:
                pass

            try:                
                return float(obj)
            except ValueError:
                pass

            if Helpers.can_be_tuple(obj):
                return Helpers.str_to_tuple(obj)


        return obj
