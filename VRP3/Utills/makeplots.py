import pandas as pd
import os
from matplotlib import pyplot as plt

def make_bars(csv_path: str, histo_path: str)-> None:
    if not os.path.exists(histo_path):
        os.makedirs(histo_path)

    with open(csv_path, 'r') as f:
        df = pd.read_csv(f)
        # print(df)
        row_num, col_num = df.shape
        col_names = df.columns.to_list()
        # print(col_names)
        config_id = col_names[0]
        fields = col_names[1:]

        for field in fields:
            plt.figure()
            plt.bar(df[config_id], df[field])
            plt.title(f'{field.upper()}')     
            plt.xlabel('config_id')
            plt.ylabel(f'{field}')
            plt.savefig(fname=f'{histo_path}/{field}')