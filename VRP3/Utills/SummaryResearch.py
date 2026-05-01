import os
import csv
import sys
import re
import json
from Utills.Helpers import Helpers
from Utills.VRP_saver import VRP_saver
import pandas as pd
import os
import re


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
    def aggregate(folder_name, subfolder_name, file_name):
        # 1. Przygotowanie ścieżek
        results_dir = VRP_saver.set_folder(folder_name, subfolder_name)
        src_path = os.path.join(results_dir, f"{file_name}.csv")
        dst_path = os.path.join(results_dir, f"{file_name}_summary.csv")

        # 2. Sprawdzenie czy plik źródłowy istnieje
        if not os.path.exists(src_path):
            print(f"❌ Plik źródłowy NIE istnieje: {src_path}")
            return
        else:
            print(f"✅ Plik źródłowy znaleziony. Rozpoczynam agregację danych...")

        try:
            # 3. Wczytanie danych
            df = pd.read_csv(src_path)

            # 4. Definicja kolumn do statystyk
            # Na podstawie Twoich metryk: best_cost, best_iteration, execution_time, itp.
            metrics = [
                'best_cost', 'best_cost_minutes', 'best_iteration', 'iterations_done',
                'avg_cost_final_minutes', 'diversity_final',
                'execution_time', 'big_shakes_count'
            ]

            # 5. Grupowanie i wyliczanie statystyk
            # Tworzymy słownik agregacji: dla metryk liczymy zestaw funkcji, dla repeat liczymy rozmiar grupy
            stats_to_compute = ['min', 'max', 'mean', 'std', 'var', 'median']
            agg_dict = {m: stats_to_compute for m in metrics}
            agg_dict['repeat'] = 'count'

            # Grupowanie po config_id
            summary_df = df.groupby('config_id').agg(agg_dict)

            # 6. Spłaszczanie nazw kolumn dla pliku CSV (np. 'best_cost' + 'mean' -> 'best_cost_avg')
            # Zmieniamy 'mean' na 'avg' w nazwach kolumn, żeby pasowało do Twoich wymagań
            summary_df.columns = [
                f"{col}_{stat.replace('mean', 'avg')}" if col != 'repeat' else 'repeats_count'
                for col, stat in summary_df.columns
            ]

            # 7. Dołączenie parametrów konfiguracji (alpha, beta, itp.)
            # Wykluczamy metryki, żeby zostały same parametry wejściowe
            exclude_from_params = metrics + ['repeat', 'config_id', 'last_big_shake_iter', 'big_shakes_at_iter']
            param_cols = [c for c in df.columns if c not in exclude_from_params]
            params_df = df.groupby('config_id')[param_cols].first()

            # Łączymy parametry ze statystykami w jedną tabelę
            final_table = pd.concat([params_df, summary_df], axis=1)

            # --- NOWA LOGIKA USTAWIANIA KOLEJNOŚCI KOLUMN ---
            # 1. Wyciągamy 'repeats_count' i parametry (alpha, beta, itp.)
            # 2. Wyciągamy resztę statystyk
            all_cols = list(final_table.columns)

            # Tworzymy listę w nowej kolejności:
            # Zaczynamy od repeats_count, potem parametry, potem reszta statystyk
            new_order = ['repeats_count'] + [c for c in all_cols if c != 'repeats_count']
            final_table = final_table[new_order]

            # 8. ZAPIS DO CSV
            final_table.to_csv(dst_path, index=True)  # index=True zachowa config_id jako pierwszą kolumnę
            print(f"💾 Zapisano podsumowanie CSV: {dst_path}")

        except Exception as e:
            print(f"❌ Wystąpił błąd: {e}")
            import traceback
            traceback.print_exc()

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
            

    @staticmethod
    def get_comparable_columns():
        return [
            "best_cost_min", "best_cost_max", "best_cost_avg", "best_cost_std", "best_cost_var", "best_cost_median",
            "best_cost_minutes_min", "best_cost_minutes_max", "best_cost_minutes_avg", "best_cost_minutes_std",
            "best_cost_minutes_var", "best_cost_minutes_median",
            "best_iteration_min", "best_iteration_max", "best_iteration_avg", "best_iteration_std",
            "best_iteration_var", "best_iteration_median",
            "iterations_done_min", "iterations_done_max", "iterations_done_avg", "iterations_done_std",
            "iterations_done_var", "iterations_done_median",
            "avg_cost_final_minutes_min", "avg_cost_final_minutes_max", "avg_cost_final_minutes_avg",
            "avg_cost_final_minutes_std", "avg_cost_final_minutes_var", "avg_cost_final_minutes_median",
            "diversity_final_min", "diversity_final_max", "diversity_final_avg", "diversity_final_std",
            "diversity_final_var", "diversity_final_median",
            "execution_time_min", "execution_time_max", "execution_time_avg", "execution_time_std",
            "execution_time_var", "execution_time_median",
            "big_shakes_count_min", "big_shakes_count_max", "big_shakes_count_avg", "big_shakes_count_std",
            "big_shakes_count_var", "big_shakes_count_median"
        ]
    
    @staticmethod
    def get_comparable_columns():
        return [
            "best_cost_min", "best_cost_max", "best_cost_avg", "best_cost_std", "best_cost_var", "best_cost_median",
            "best_cost_minutes_min", "best_cost_minutes_max", "best_cost_minutes_avg", "best_cost_minutes_std",
            "best_cost_minutes_var", "best_cost_minutes_median",
            "best_iteration_min", "best_iteration_max", "best_iteration_avg", "best_iteration_std",
            "best_iteration_var", "best_iteration_median",
            "iterations_done_min", "iterations_done_max", "iterations_done_avg", "iterations_done_std",
            "iterations_done_var", "iterations_done_median",
            "avg_cost_final_minutes_min", "avg_cost_final_minutes_max", "avg_cost_final_minutes_avg",
            "avg_cost_final_minutes_std", "avg_cost_final_minutes_var", "avg_cost_final_minutes_median",
            "diversity_final_min", "diversity_final_max", "diversity_final_avg", "diversity_final_std",
            "diversity_final_var", "diversity_final_median",
            "execution_time_min", "execution_time_max", "execution_time_avg", "execution_time_std",
            "execution_time_var", "execution_time_median",
            "big_shakes_count_min", "big_shakes_count_max", "big_shakes_count_avg", "big_shakes_count_std",
            "big_shakes_count_var", "big_shakes_count_median"
        ]
    
    @staticmethod
    def get_param_names():
        return {        
            'ACO_3': [
                "ants",
                "iterations",
                "alpha",
                "beta",
                "evaporation",
                "patience",
                "patience_big_shake",
                "big_shake_evaporation",
                "big_shake_duration",
                "intensity_big_shake",
                "tau_min",
                "tau_max"
            ],
            'ACO_4': [
                "ants",
                "iterations",
                "alpha",
                "beta",
                "evaporation",
                "patience",
                "patience_big_shake",
                "big_shake_evaporation",
                "big_shake_duration",
                "intensity_big_shake",
                "tau_min",
                "tau_max",
                "patience_small_shake",
                "intensity_small_shake",
                "intensity_elite_ant",
                "ranked_ants_count",
                "q_pheromone",
            ]
        }
    
    @staticmethod        
    def find_best_in_category(src_path, dst_path):
        # Sprawdza czy dana ścieżka jest poprawna
        if not os.path.exists(src_path):
            print(f"Warning! {src_path} doesn't exist")
            return
        
        if not re.search(r'\.csv$', src_path):
            print(f"Warning! {src_path} must be csv")
            return

        # Sprawdza wersję ACO
        ACO_version = ''

        if re.search(r'(ACO_3)|(aco_3)|(Aco_3)|(ACO3)|(aco3)|(Aco3)', src_path):
            ACO_version = 'ACO_3'
        elif re.search(r'(ACO_4)|(aco_4)|(Aco_4)|(ACO4)|(aco4)|(Aco4)', src_path):  
            ACO_version = 'ACO_4'
        else:
            print(f'Nie ma zapisanych parametrów dla {ACO_version.group()}')

        to_json = {}

        with open(src_path, 'r') as f:
            df = pd.read_csv(f)

            comparable_columns = SummaryResearch.get_comparable_columns()
            params = SummaryResearch.get_param_names()[ACO_version]

            for comparable in comparable_columns:                
                to_json[comparable] = {'params': {}}

                idx = pd.Series.idxmin(df[comparable])

                for col_name, val in df.iloc[idx].items():
                    if col_name in params:
                        to_json[comparable]['params'][col_name] = val
                    else:
                        to_json[comparable][col_name] = val
                
        VRP_saver.save_json(dst_path, to_json, verbose=True)           
            


