# Modules
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui


import datetime
import pandas as pd
import logging
import random
import os
import shutil
import sys
import requests


# Main Folder
from local_functions.main import algo
from local_functions.main import log_funcs
from local_functions.main import reset_vars

# Analyse
from local_functions.analyse import analyse
from local_functions.analyse import common
from local_functions.analyse import order_eval
from local_functions.analyse import order_tools
from local_functions.analyse import update_docs

# Account Info
from local_functions.account import account_info as account

# Data Management
from local_functions.data_management import gather_data as gather
from local_functions.data_management import stock_screening as screen
from local_functions.data_management import historical_funcs as hist

# Trade Functions
from local_functions.trade_funcs import sim_executions as sim_exe
from local_functions.trade_funcs import trade_funcs

# from local_functions.live_graph import candles as candles
# from local_functions.td_api import api_chart

from local_functions.plotting import plot_results as plotr

# Stock info.
stock_pick = 'nan'
trade_mode = 'nan'


order_count = 0
pos_update = False
loop_feedback = True
sell_out = False
chart_response = False
buy_clock = 0
buy_lock = False


# CSV Trading
sim_df = 'Dataframe'
csv_indexes = 'dictionary'
minute_prices = 'list'
minute_volumes = 'list'
batch_frame = 'Dataframe'

# will be defined first by reset func, then updated.
order_specs = 'Dataframe'
queued_orders = 'Dataframe'
open_orders = 'Dataframe'
cancelled_orders = 'Dataframe'
current_positions = 'Dataframe'
filled_orders = 'Dataframe'
current_frame = 'Dataframe'
mom_frame = 'Dataframe'
sup_res_frame = 'Dataframe'
log = 'Dataframe'

current = 'dictionary'
last = 'dictionary'
pl_ex = 'dictionary'
volas = 'dictionary'
volumes = 'dictionary'


def csv_to_dict(file_path):
    df = pd.read_csv(file_path)
    df = df.set_index('type')
    df = df[['value']]
    dictionary = df.to_dict()['value']
    return dictionary


def save_dict_to_csv(dictionary, file_name):
    df = pd.DataFrame(dictionary, index=['value']).T
    df = df.reset_index().rename(columns={'index': 'type'})
    save_frame(df, file_name)


def save_frame(dataframe, file_name):
    dataframe.to_csv(filepath[file_name])


filepath = {
    'current': r'temp_assets\current.csv',
    'pl_ex': r'temp_assets\pl_and_ex.csv',
    'volas': r'temp_assets\volas.csv',
    'current_frame': r'temp_assets\current_frame.csv',
    'mom_frame': r'temp_assets\mom_frame.csv',
    'sup_res_frame': r'temp_assets\supports_resistances.csv',
    'current_positions': r'temp_assets\current_positions.csv',
    'filled_orders': r'temp_assets\filled_orders.csv',
    'open_orders': r'temp_assets\open_orders.csv',

    'log': r'temp_assets\log.csv',
    'efficiency_log': r'temp_assets\efficiency_log.csv',
}


def clear_temp_assets():
    import os
    import shutil
    folder = 'temp_assets'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def save_all():
    '''
    ### Save All Files
    Once trading is done, save all global variables as csv files. 
    '''
    files = {

        'current': current,
        'pl_ex': pl_ex,
        'current_frame': current_frame,
        'mom_frame': mom_frame,
        'sup_res_frame': sup_res_frame,
        'volas': volas,
        'current_positions': current_positions,
        'filled_orders': filled_orders,
        'open_orders': open_orders,
        'log': log,

    }
    clear_temp_assets()
    for file_name, file in zip(files.keys(), files.values()):

        if type(file) == dict:
            save_dict_to_csv(file, file_name)
        else:
            save_frame(file, file_name)

    if len(filled_orders) != 0:
        plotr.plot_results(current_frame, filled_orders)
