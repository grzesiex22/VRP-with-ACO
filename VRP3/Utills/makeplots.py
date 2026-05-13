import pandas as pd
import os
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


# def summary_bars(plot_dir_path):
#     if not os.path.exists(plot_dir_path):
#         os.makedirs(plot_dir_path, exist_ok=True)

#     greedy_df = pd.read_csv('Results/Dataset_tests/greedy_experiments.csv')
#     aco_3_df = pd.read_csv('Results/Dataset_tests/ACO_3_experiments_summary.csv')
#     aco_4_df = pd.read_csv('Results/Dataset_tests/ACO_4_experiments_summary.csv')

#     greedy_df['n'] = 20 * (greedy_df["config_id"] // 8 + 1)
#     aco_3_df['n'] = 20 * (aco_3_df["config_id"] // 8 + 1)
#     aco_4_df['n'] = 20 * (aco_4_df["config_id"] // 8 + 1)

#     for i in range(20, 81, 20):
#         greedy_agg = greedy_df.loc[greedy_df['n'] == i, ['config_id', 'cost']]
#         aco_3_agg = aco_3_df.loc[aco_3_df['n'] == i, ['config_id','cost_avg', 'cost_min', 'cost_max', 'cost_std']]
#         aco_4_agg = aco_4_df.loc[aco_4_df['n'] == i, ['config_id','cost_avg', 'cost_min', 'cost_max', 'cost_std']]

#         ns = [j for j in range(8)]
#         x = np.arange(len(ns))
#         width = 0.25

#         fig, ax = plt.subplots(figsize=(10, 6))

#         # --- słupki ---
#         b1 = ax.bar(x - width, greedy_agg['cost'], width, label='Greedy')
#         b2 = ax.bar(x, aco_3_agg['cost_avg'], width, label='ACO-3')
#         b3 = ax.bar(x + width, aco_4_agg['cost_avg'], width, label='ACO-4')

#         # --- error bary ---
#         ax.errorbar(
#             x,
#             aco_3_agg['cost_avg'],
#             yerr=aco_3_agg['cost_std'],
#             fmt='none',
#             ecolor='black',
#             capsize=5
#         )

#         ax.errorbar(
#             x + width,
#             aco_4_agg['cost_avg'],
#             yerr=aco_4_agg['cost_std'],
#             fmt='none',
#             ecolor='black',
#             capsize=5
#         )

#         # --- opis ---
#         ax.set_ylabel('Cost mean')
#         ax.set_xlabel('config_id')
#         ax.set_title(f'Porównanie algorytmów dla n={i}')
#         ax.set_xticks(x, ns)
#         ax.legend()

#         plt.tight_layout()

#         full_path = os.path.abspath(f"{plot_dir_path}/summary_bars_{i}.png")
#         plt.savefig(full_path)
#         plt.close()




# def summary_bars(plot_dir_path):
#     if not os.path.exists(plot_dir_path):
#         os.makedirs(plot_dir_path, exist_ok=True)

#     greedy_df = pd.read_csv('Results/Dataset_tests/greedy_experiments.csv')
#     aco_3_df = pd.read_csv('Results/Dataset_tests/ACO_3_experiments_summary.csv')
#     aco_4_df = pd.read_csv('Results/Dataset_tests/ACO_4_experiments_summary.csv')

#     greedy_df['n'] = 20 * (greedy_df["config_id"] // 8 + 1)
#     aco_3_df['n'] = 20 * (aco_3_df["config_id"] // 8 + 1)
#     aco_4_df['n'] = 20 * (aco_4_df["config_id"] // 8 + 1)

#     for i in range(20, 81, 20):
#         greedy_agg = greedy_df.loc[greedy_df['n'] == i, ['config_id', 'cost']]
#         aco_3_agg = aco_3_df.loc[aco_3_df['n'] == i, ['config_id','cost_avg', 'cost_min', 'cost_max', 'cost_std']]
#         aco_4_agg = aco_4_df.loc[aco_4_df['n'] == i, ['config_id','cost_avg', 'cost_min', 'cost_max', 'cost_std']]

#         ns = greedy_agg['config_id'].tolist()
#         x = np.arange(len(ns))
#         width = 0.25

#         fig, ax = plt.subplots(figsize=(10, 6))

#         # --- słupki ---
#         ax.bar(x - width, greedy_agg['cost'], width, label='Greedy')
#         ax.bar(x, aco_3_agg['cost_avg'], width, label='ACO-3')
#         ax.bar(x + width, aco_4_agg['cost_avg'], width, label='ACO-4')

#         # --- error bary: min/max ---
#         # ACO-3
#         aco3_lower = aco_3_agg['cost_avg'] - aco_3_agg['cost_min']
#         aco3_upper = aco_3_agg['cost_max'] - aco_3_agg['cost_avg']

#         ax.errorbar(
#             x,
#             aco_3_agg['cost_avg'],
#             yerr=[aco3_lower, aco3_upper],
#             fmt='none',
#             ecolor='black',
#             capsize=5
#         )

#         # ACO-4
#         aco4_lower = aco_4_agg['cost_avg'] - aco_4_agg['cost_min']
#         aco4_upper = aco_4_agg['cost_max'] - aco_4_agg['cost_avg']

#         ax.errorbar(
#             x + width,
#             aco_4_agg['cost_avg'],
#             yerr=[aco4_lower, aco4_upper],
#             fmt='none',
#             ecolor='black',
#             capsize=5
#         )

#         # --- opis ---
#         ax.set_ylabel('Cost mean')
#         ax.set_xlabel('config_id')
#         ax.set_title(f'Porównanie algorytmów dla n={i}')
#         ax.set_xticks(x, ns)
#         ax.legend()

#         plt.tight_layout()

#         full_path = os.path.abspath(f"{plot_dir_path}/summary_bars_{i}.png")
#         plt.savefig(full_path)
#         plt.close()



def summary_bars(plot_dir_path):
    if not os.path.exists(plot_dir_path):
        os.makedirs(plot_dir_path, exist_ok=True)

    greedy_df = pd.read_csv('Results/Dataset_tests/greedy_experiments.csv')
    aco_3_df = pd.read_csv('Results/Dataset_tests/ACO_3_experiments_summary.csv')
    aco_4_df = pd.read_csv('Results/Dataset_tests/ACO_4_experiments_summary.csv')

    # grupowanie po n
    for df in (greedy_df, aco_3_df, aco_4_df):
        df['n'] = 20 * (df["config_id"] // 8 + 1)

    for i in range(20, 81, 20):
        greedy_agg = greedy_df.loc[greedy_df['n'] == i, ['config_id', 'cost']]
        aco_3_agg = aco_3_df.loc[aco_3_df['n'] == i, ['config_id','cost_avg', 'cost_min', 'cost_max', 'cost_std']]
        aco_4_agg = aco_4_df.loc[aco_4_df['n'] == i, ['config_id','cost_avg', 'cost_min', 'cost_max', 'cost_std']]

        ns = list(range(8))
        x = np.arange(len(ns))
        width = 0.25

        fig, ax = plt.subplots(figsize=(10, 6))

        # --- słupki mean (z labelami!) ---
        greedy_bar = ax.bar(x - width, greedy_agg['cost'], width, label='Greedy')
        aco3_bar   = ax.bar(x,         aco_3_agg['cost_avg'], width, label='ACO-3')
        aco4_bar   = ax.bar(x + width, aco_4_agg['cost_avg'], width, label='ACO-4')

        # --- std ---
        ax.errorbar(x, aco_3_agg['cost_avg'], yerr=aco_3_agg['cost_std'],
                    fmt='none', ecolor='black', capsize=4, linewidth=1)
        ax.errorbar(x + width, aco_4_agg['cost_avg'], yerr=aco_4_agg['cost_std'],
                    fmt='none', ecolor='black', capsize=4, linewidth=1)

        # --- min/max ---
        ax.hlines(aco_3_agg['cost_min'], x - 0.05, x + 0.05, colors='cyan', linewidth=2)
        ax.hlines(aco_3_agg['cost_max'], x - 0.05, x + 0.05, colors='red', linewidth=2)

        ax.hlines(aco_4_agg['cost_min'], (x + width) - 0.05, (x + width) + 0.05, colors='cyan', linewidth=2)
        ax.hlines(aco_4_agg['cost_max'], (x + width) - 0.05, (x + width) + 0.05, colors='red', linewidth=2)

        # --- opis ---
        ax.set_ylabel('Cost')
        ax.set_xlabel('config_id')
        ax.set_title(f'Porównanie algorytmów dla n={i}')
        ax.set_xticks(x, ns)

        # --- proxy artists ---
        std_line = Line2D([0], [0], color='black', linewidth=1, marker='_', markersize=10, label='Std')
        min_line = Line2D([0], [0], color='cyan', linewidth=2, label='Min')
        max_line = Line2D([0], [0], color='red', linewidth=2, label='Max')

        ax.legend(handles=[greedy_bar, aco3_bar, aco4_bar, std_line, min_line, max_line])

        plt.tight_layout()
        plt.savefig(os.path.join(plot_dir_path, f"summary_bars_{i}.png"))
        plt.close()
