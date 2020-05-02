# region Modules

# import pyqtgraph as pg
# from pyqtgraph import QtCore, QtGui


import datetime
import pandas as pd
import logging
import random
import os
import shutil
import sys
# import requests
from functools import wraps
from pathlib import Path


# Main Folder
from local_functions.main import algo
from local_functions.main import log_funcs
from local_functions.main import controls

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

# endregion imports

directory = Path(os.getcwd())

# Stock info.
stock_pick = 'nan'
trade_mode = 'nan'

# used for order ids.
order_count = 0
pos_update = False
loop_feedback = True
sell_out = False
chart_response = False
buy_clock = 0
buy_lock = False


# CSV Trading
batch_path = 'string'
sim_df = 'Dataframe'
csv_indexes = 'dictionary'
minute_prices = 'list'
minute_volumes = 'list'
batch_frame = 'Dataframe'

# region Frames
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
# endregion Frames

current = 'dictionary'
last = 'dictionary'
pl_ex = 'dictionary'
volas = 'dictionary'
volumes = 'dictionary'

open_cancels = {}


# region Controls/Configurations

sell_conditions = []
buy_conditions = []


# endregion Controls/Configurations


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


def save_frame(df, file_name):

    page_names = {

        'log': 'Log',
        'filled_orders': 'Filled Orders',
        'current_positions': 'Current Positions',
        'open_orders': 'Open Orders',
        'mom_frame': 'Momentum Frame',
        'current_frame': 'Current Frame',
        'order_specs': 'Order Specifications',
        'pl_ex': 'P/L and Exposure',
        'sup_res_frame': 'Supports and Resistances',
        'volas': 'Volatility',
        'volumes': 'Volume',
        'cancelled_orders': 'Cancelled Orders',
        'queued_orders': 'Queued Orders',
        'current': 'Current',
    }

    def tag(text, tag, attrs=None, text_in_tag=False):
        if text_in_tag == True:
            return f'<{tag} {text}></{tag}>'

        start_tag = f'<{tag}>'
        if attrs != False:
            start_tag = f'<{tag} {attrs}>'
        end_tag = f'</{tag}>'
        return start_tag+text+end_tag

    # df = pd.read_csv('temp_assets/log.csv')
    table = df.to_html(classes='alt', table_id='df_to_dt')
    table = tag(table, 'div', 'class="display"')

    template = str(directory / 'batch_design' / 'table_template.html')
    with open(template, 'r') as file:
        text = file.read()

    asset_path = str(directory / 'batch_design' / 'assets')

    index_path = str(batch_path / 'batch_index.html')

    text = text.replace('^^^doc_name^^^', page_names[file_name])
    text = text.replace('^^^asset_path^^^', asset_path)
    text = text.replace('^^^index_path^^^', index_path)
    text = text.replace('<!-- table_insert -->', table)

    dst = directory / 'temp_assets' / f'{file_name}.html'

    with open(dst, 'x') as file:
        file.write(text)


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
        'volas': volas,
        'volumes': volumes,

        'current_frame': current_frame,
        'mom_frame': mom_frame,
        'sup_res_frame': sup_res_frame,


        'order_specs': order_specs,
        'queued_orders': queued_orders,
        'cancelled_orders': cancelled_orders,
        'open_orders': open_orders,
        'current_positions': current_positions,
        'filled_orders': filled_orders,

        'log': log,

    }
    clear_temp_assets()
    for file_name, file in zip(files.keys(), files.values()):

        if type(file) == dict:
            save_dict_to_csv(file, file_name)
        else:
            save_frame(file, file_name)

    if len(mom_frame) != 0:
        html_path = str(directory / 'temp_assets' / 'mom_tracking.html')
        plotr.plot_momentum(mom_frame, current_frame, html_path)
    if len(filled_orders) != 0:
        plotr.plot_results(current_frame, filled_orders)


def save_on_error(orig_func):
    # region Docstring
    '''
    # Save on Error
    ## Decorator Function
    Saves all global variables to the temp assets folder whenever there is an error

    Also prints out the traceback. 

    '''
    # endregion Docstring
    @ wraps(orig_func)
    def wrapper(*args, **kwargs):
        import traceback
        try:
            orig_func(*args, **kwargs)
        except:
            trace = traceback.format_exc()
            print('\n\nError Occurred\n')
            save_all()
            print('global variables saved to temp_assets.\n')
            # print(trace)
            trace_path = directory / 'temp_assets' / 'trace.txt'
            with open(trace_path, 'x') as file:
                file.writelines(trace)
                # trace = file.readlines()
                file.close()

            trace = trace.split('\n')
            simple_traceback(trace)
    return wrapper


def simple_traceback(trace):
    l = trace
    del l[0]
    error = l[-2]
    del l[-1]
    del l[-1]

    paths = []
    lns = []
    funcs = []
    codes = []
    for line in l:
        line = line.strip()
        if line.startswith('File'):
            path, ln, func = line.split(',')
            path = os.path.basename(path)
            ln = ln.split('line ')[1]
            func = func.split('in ')[1].split('\n')[0]
            paths.append(path)
            lns.append(ln)
            funcs.append(func)
        else:
            codes.append(line)

    frame = {
        'code': codes,
        'line': lns,
        'file': paths,
        'function': funcs,
    }
    print(error)
    df = pd.DataFrame(frame)
    pd.set_option('display.max_colwidth', -1)
    df = df.sort_index(ascending=False)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        if isnotebook():
            display(df)
        else:
            print(df)


def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter
