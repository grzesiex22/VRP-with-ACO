import ast
import os
import csv
import sys
import re
import json

import numpy as np
from Utills.Helpers import Helpers
from Utills.VRP_saver import VRP_saver
import pandas as pd
import os
import re


class SummaryResearch:

    @staticmethod
    def _clean_types(row_dict):
        """Pomocnicza funkcja do naprawy typów po wczytaniu z CSV/JSON"""
        to_int_keys = [
            'config_id', 'repeats_count', 'repeat', 'repeats', 'ants', 'iterations',
            'patience', 'patience_small_shake', 'patience_big_shake',
            'big_shake_duration', 'best_iteration_min', 'best_iteration_max',
            'iterations_done_min', 'iterations_done_max', 'big_shakes_count_min',
            'big_shakes_count_max'
        ]
        to_float_keys = [
            'alpha', 'beta', 'evaporation', 'big_shake_evaporation',
            'intensity_small_shake', 'intensity_big_shake', 'intensity_elite_ant',
            'q_pheromone', 'tau_min', 'tau_max'
        ]

        cleaned = {}
        for k, v in row_dict.items():
            # 1. Obsługa krotek/list (np. ranked_ants_count)
            if k == 'ranked_ants_count' and isinstance(v, str):
                try:
                    v = ast.literal_eval(v)
                except:
                    pass

            # 2. Wymuszenie INT
            elif k in to_int_keys:
                try:
                    v = int(float(str(v)))
                except:
                    pass

            # 3. Wymuszenie FLOAT
            elif k in to_float_keys:
                try:
                    v = float(v)
                except:
                    pass

            cleaned[k] = v
        return cleaned

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
    def get_best_aco_config(folder_name, subfolder_name, src_file_name, feature='avg_cost'):
        results_dir = VRP_saver.set_folder(folder_name, subfolder_name)
        src_path = os.path.join(results_dir, src_file_name)

        if not os.path.exists(src_path):
            print(f"❌ Warning! {src_path} doesn't exist")
            return None

        best_aco_config = {'params': {}}

        # --- OBSŁUGA PLIKU CSV ---
        if src_path.endswith('.csv'):
            df = pd.read_csv(src_path)
            if 'best_for_category' in df.columns:
                best_row_df = df[df['best_for_category'] == feature]
                if not best_row_df.empty:
                    # Wczytujemy surowy słownik z Pandas
                    raw_dict = best_row_df.iloc[0].to_dict()
                    # CZYŚCIMY TYPY!
                    row_dict = SummaryResearch._clean_types(raw_dict)

                    aco_ver = 'ACO_3' if 'ACO_3' in src_file_name.upper() else 'ACO_4'
                    param_names = SummaryResearch.get_param_names()[aco_ver]

                    for col, val in row_dict.items():
                        if col in param_names:
                            best_aco_config['params'][col] = val
                        else:
                            best_aco_config[col] = val

                    print(f"✅ Wczytano (i naprawiono typy) z CSV: {feature}")
                    return best_aco_config

        # --- OBSŁUGA PLIKU JSON ---
        elif src_path.endswith('.json'):
            with open(src_path, 'r') as f:
                from_json = json.load(f)
                if feature in from_json:
                    data = from_json[feature]

                    # Zamiast Helpers.convert, używamy naszego czyszczenia dla sekcji params
                    if 'params' in data:
                        data['params'] = SummaryResearch._clean_types(data['params'])

                    # Czyścimy też resztę (statystyki poza params)
                    data = SummaryResearch._clean_types(data)

                    print(f"✅ Wczytano z JSON: {feature}")
                    return data

        return None

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
    def find_best_in_category(folder_name, subfolder_name, src_file_name, dst_file_name_json, dst_file_name_csv):
        results_dir = VRP_saver.set_folder(folder_name, subfolder_name)
        src_path = os.path.join(results_dir, src_file_name)

        # Przygotowanie ścieżek wyjściowych
        dst_json = os.path.join(results_dir, dst_file_name_json)
        dst_csv = os.path.join(results_dir, dst_file_name_csv)

        if not os.path.exists(src_path):
            print(f"❌ Warning! {src_path} doesn't exist")
            return None

        if not re.search(r'\.csv$', src_path):
            print(f"❌ Warning! {src_path} must be csv")
            return None

        # Rozpoznawanie wersji ACO
        if re.search(r'ACO_?3', src_path, re.IGNORECASE):
            ACO_version = 'ACO_3'
        elif re.search(r'ACO_?4', src_path, re.IGNORECASE):
            ACO_version = 'ACO_4'
        else:
            print(f"❌ Nie rozpoznano wersji ACO w nazwie pliku.")
            return None

        # Wczytanie danych
        df = pd.read_csv(src_path)
        comparable_columns = SummaryResearch.get_comparable_columns()
        param_names = SummaryResearch.get_param_names()[ACO_version]

        to_json = {}
        rows_for_csv = []

        for category in comparable_columns:
            if category not in df.columns:
                continue

            idx = df[category].idxmin()

            # UŻYCIE FUNKCJI CZYSZCZĄCEJ
            best_row = SummaryResearch._clean_types(df.iloc[idx].to_dict())

            # --- LOGIKA DLA JSON ---
            to_json[category] = {'params': {}}
            for col_name, val in best_row.items():
                if col_name in param_names:
                    to_json[category]['params'][col_name] = val
                else:
                    to_json[category][col_name] = val

            # --- LOGIKA DLA CSV ---
            csv_row = {'best_for_category': category}
            csv_row.update(best_row)
            rows_for_csv.append(csv_row)

        # Zapis do JSON
        VRP_saver.save_json(dst_json, to_json, verbose=True)

        # Zapis do CSV
        summary_df = pd.DataFrame(rows_for_csv)
        if 'repeat' in summary_df.columns:
            summary_df = summary_df.rename(columns={'repeat': 'repeats'})

        # Układ kolumn: [kategoria, config_id, repeats, ...]
        cols = summary_df.columns.tolist()
        important_start = ['best_for_category', 'config_id']
        if 'repeats' in cols: important_start.append('repeats')

        new_order = important_start + [c for c in cols if c not in important_start]
        summary_df = summary_df[new_order]

        summary_df.to_csv(dst_csv, index=False)
        print(f"✅ Zapisano podsumowanie najlepszych wyników do CSV: {dst_csv}")

        return to_json



