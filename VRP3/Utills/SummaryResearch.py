import os
import csv
import sys
import re
import json
from Utills.Helpers import Helpers

class SummaryResearch:
    @staticmethod
    def current_aco_config(curr_id, row, headers):
        return {
            "id": curr_id,
            "name": "ACO 3 (seq.)",
            "save_name": "ACO_3",
            "class": "ACO_for_VRP_3",
            "params": {
                "ants": row[headers['ants']],
                "iterations": row[headers['iterations']],
                "alpha": row[headers['alpha']],
                "beta": row[headers['beta']],
                "evaporation": row[headers['evaporation']],
                "patience": row[headers['patience']],
                "patience_big_shake": row[headers['patience_big_shake']],
                "big_shake_evaporation": row[headers['big_shake_evaporation']],
                "big_shake_duration": row[headers['big_shake_duration']],
                "intensity_big_shake": row[headers['intensity_big_shake']],
                "tau_min": row[headers['tau_min']],
                "tau_max": row[headers['tau_max']]
            },
            "min_cost": sys.maxsize,
            "max_cost": 0,
            "avg_cost": 0
        }

    @staticmethod
    def aggregate(src_path, dst_path, limit_rows_per_config=10):
        # Check paths
        if not os.path.exists(src_path):
            print(f"Warning! {src_path} doesn't exist")
            return

        if not re.search(r'\.csv$', src_path):
            print(f"Warning! {src_path} must be csv")
            return

        dirname, filename = dst_path.rsplit('/', maxsplit=1)

        if os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)

        if not re.search(r'\.json$', filename):
            print(f"Warning! {filename} must be json")
            return            
        
        # Extract data
        headers = {}

        with open(src_path, 'r') as src_file:
            csvreader = csv.reader(src_file)

            # get headers
            header_row = next(csvreader)
            for i, name in enumerate(header_row):
                headers[name] = i

            # get aco configurations
            curr_id = 0
            sum_cost = 0
            num_rows = 0
            max_cost = 0
            min_cost = sys.maxsize
            
            to_json = {}

            for i, row in enumerate(csvreader):
                curr_id = row[headers['config_id']] 
                
                if num_rows == 0:
                    to_json[curr_id] = SummaryResearch.current_aco_config(curr_id, row, headers)
                    # curr_id = next_id                   

                cost = float(row[headers['best_cost']])

                max_cost = max(cost, max_cost)
                min_cost = min(cost, min_cost)
                sum_cost += cost 
                num_rows += 1

                if num_rows >= limit_rows_per_config:
                    if to_json is not None:
                        to_json[curr_id]['min_cost'] = min_cost
                        to_json[curr_id]['max_cost'] = max_cost
                        to_json[curr_id]['avg_cost'] = sum_cost / num_rows

                    max_cost = 0
                    min_cost = sys.maxsize
                    sum_cost = 0
                    num_rows = 0
                    

        Helpers.save_json(dst_path, to_json, verbose=True)

    @staticmethod        
    def get_best_aco_config(src_path, feature='avg_cost'):
        if not os.path.exists(src_path):
            print(f"Warning! {src_path} doesn't exist")
            return
        
        if not re.search(r'\.json$', src_path):
            print(f"Warning! {src_path} must be json")
            return       

        best_aco_config = None

        with open(src_path, 'r') as f:
            from_json = json.load(f)

            for config in from_json.values():
                if best_aco_config is None:
                    best_aco_config = config
                    continue
                
                try:
                    if float(best_aco_config[feature]) > float(config[feature]):
                        best_aco_config = config
                except:
                    pass

        best_aco_config = Helpers.convert(best_aco_config)
        
        return best_aco_config
            

            


