# region Modules

import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

import numpy as np
import json
import datetime
import pandas as pd
import logging
import random
import os
import shutil
import sys
import requests
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
from local_functions.plotting import candles
from local_functions.plotting import api_chart

# endregion imports

directory = Path(os.getcwd())
config = 'default'

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
csv_name = 'string'
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


def save_dict_to_frame(dictionary, file_name):
    # region Docstring
    '''
    # Save Dictionary to Frame
    Converts dictionary to DataFrame. then uses the `save_frame` function. 

    ## Parameters:{
    ####    `dictionary`: dict to be converted 
    ####    `file_name`: file name of dict
    ## }
    '''
    # endregion Docstring
    df = pd.DataFrame(dictionary, index=['value']).T
    df = df.reset_index().rename(columns={'index': 'type'})
    save_frame(df, file_name)


def save_frame(df, file_name):
    # region Docstring
    '''
    # Save Frame
    Takes a dataframe and converts it to an html file using a template. 

    ## Parameters:{
    ####    `df`: dataframe to save
    ####    `file_name`: name of df
    ## }

    '''
    # endregion Docstring

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

    table = frame_to_html(df, file_name)

    template = str(directory / 'batch_design' / 'table_template.html')
    with open(template, 'r') as file:
        text = file.read()

    asset_path = str(directory / 'batch_design' / 'assets')
    index_path = str(batch_path / 'batch_index.html')

    text = text.replace('^^^doc_name^^^', page_names[file_name])
    text = text.replace('^^^csv_name^^^', csv_name)
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
    # region Docstring
    '''
    # Clear Temp Assets
    Deletes all items in the temp_assets folder. 

    ## Process:

    ### 1)

    ## Notes:
    - Notes

    ## TO DO:
    - Item
    '''
    # endregion Docstring
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


def save_config():
    # region Docstring
    '''
    # Save Config
    saves config.json used for trading in the temp_assets

    #### Returns nothing, saves the json file. 

    '''
    # endregion Docstring
    global config
    if config == 'default':
        from config.ipy_creator import make_default_config_json, sp, bp, misc
        config = make_default_config_json(False)
    else:
        import json
        config = json.dumps(config, indent=4, sort_keys=True)

    path = directory / 'temp_assets' / 'config.json'
    with open(path, 'x') as f:
        f.write(config)
        f.close()

    config = 'default'


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
    save_config()
    for file_name, file in zip(files.keys(), files.values()):

        if type(file) == dict:
            save_dict_to_frame(file, file_name)
        else:
            save_frame(file, file_name)

    if len(mom_frame) != 0:
        update_docs.update_momentum()
        html_path = str(directory / 'temp_assets' / 'mom_tracking.html')
        plotr.plot_momentum(mom_frame, current_frame,
                            directory, batch_path, csv_name)
    if len(filled_orders) != 0:
        plotr.plot_results(current_frame, filled_orders,
                           batch_path, directory, csv_name)


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
    # region Docstring
    '''
    # Simple Traceback
    ### Creates a simplified traceback for troubleshooting. 
    '''
    # endregion Docstring

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
    # region Docstring
    '''
    # Is Notebook
    Checks to see if the code is running in an ipython kernel or in the terminal

    Returns True if running in a notebook. 
    '''
    # endregion Docstring
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


def frame_to_html(df, df_name):
    # region Docstring
    '''
    # Frame to HTML
    Converts Dataframe to an HTML table that will work with 

    Returns html table element. 

    ## Parameters:{
    ####    `df`: global variable df
    ####    `df_name`: global variable name. 
    ## }

    '''
    # endregion Docstring

    indexes = {
        'batch_frame': 'tick_date',
        'log': 'minute',
        'filled_order': 'exe_time',
        'volas': 'type',
        'sup_res_frame': 'type',
        'current_frame': 'ticker',
        'cancelled_orders': 'ticker',
        'current_positions': 'exe_time',
        'cancelled_orders': 'order_id',
        'order_specs': 'order_id',
        'order_specs': 'order_id',
        'open_orders': 'order_id',
        'queued_orders': 'order_id',
    }

    def tag(text, tag, attrs=None, text_in_tag=False):
        if text_in_tag == True:
            return f'<{tag} {text}></{tag}>'

        start_tag = f'<{tag}>'
        if attrs != False:
            start_tag = f'<{tag} {attrs}>'
        end_tag = f'</{tag}>'
        return start_tag+text+end_tag

    if df_name in indexes.keys():
        if len(df) != 0:
            df = df.set_index(indexes[df_name], drop=True)

    table = df.to_html(classes='alt', table_id='df_to_dt')
    table = tag(table, 'div', 'class="display"')
    return table


def manage_algo_config_repo(method):
    # region Docstring
    '''
    # Manage algo_config repo
    group of functions for interacting with the algo_config repo on github. 

    #### Returns depends on method

    ## Parameters:{
    ####    `method`: str, relates to function to call:
    -               `update`: updates the template, default.json and colab.ipynb,
    -               `delete`: remove all config files from created folder in repo but file
                            can still be found in commit history,
    -               `get_repo`: returns github repo object,
    -               `get_files`: returns list of content objects for each json,
    -               `pick`: allows user to pick which file they would like to see. 

    ## }
    '''
    # endregion Docstring
    from config import ipy_creator

    def update_config_files():
        # region Docstring
        '''
        # Update Config Files
        Updates the algo_config repo on github, creating a new ipynb, default json, and template 
        for testing based on current control.py settings.

        #### Returns nothing, saves to github.

        '''
        # endregion Docstring
        path = directory
        repo = get_algo_config_repo()
        ipy_creator.update_all(path, repo)

    def delete_all_created_configs():
        # region Docstring
        '''
        # Delete All Created Configs
        deletes all creates config.json files in github repo

        #### Returns nothing
        '''
        # endregion Docstring
        repo = get_algo_config_repo()
        created = repo.get_contents('created')
        if len(created) != 0:
            for f in created:
                commit_msg = f"removed {f}"
                repo.delete_file(f.path, commit_msg, f.sha, branch="master")
                print(commit_msg)

    def get_algo_config_repo():
        # region Docstring
        '''
        # Get algo_config repo
        retrieves the repo object using the pygithub package.  

        #### Returns repo object.

        note: got an email saying that login with u/p will be deprecated soon. 
        '''
        # endregion Docstring
        from github import Github
        user, pasw = 'dcorso21', 'PFgyMWEVJQnZzu2'
        g = Github(user, pasw)
        for repo in g.get_user().get_repos():
            if str(repo) == 'Repository(full_name="dcorso21/algo_config")':
                break
        return repo

    def get_config_files():
        # region Docstring
        '''
        # Get Config Files
        gets all listed config.json files in repo.

        #### Returns list of github content files which can be converted to dicts.  
        '''
        # endregion Docstring
        repo = get_algo_config_repo()
        files = list(repo.get_contents('created'))
        files.reverse()
        return files

    def pick_config_file():
        # region Docstring
        '''
        # Pick Config File
        prompts to 

        #### Returns chosen config files

        '''
        # endregion Docstring
        files = get_config_files()
        get_df_view(files)
        prompt = 'please specify config by number (for default put -1)'
        num = int(input(prompt))
        if num == -1:
            return 'default'
        return files[num]

    def view_config_file():
        c = pick_config_file()
        if c == 'default':
            c = ipy_creator.make_default_config_json(path = False)
        else:
            c = c.decoded_content
            c = json.loads(c)
            c = json.dumps(c, indent = 4, sort_keys=True)
        print(c)

    def get_df_view(files = get_config_files()):
        df = pd.DataFrame()
        for f in files:
            flist = f.name.split('created/')[0].split('_',3)
            fn = flist[3:][0]
            if fn == '.json':
                fn = 'no name'
            else:
                fn = fn.split('.json')[0]
            row = {
                'name': [fn],
                'date': [flist[0]],
                'time': [f'{flist[1]} {flist[2]}'],
            }
            dfx = pd.DataFrame(row)
            df = df.append(dfx, sort = False)

        df = df.reset_index(drop=True)
        if isnotebook():
            display(df)
        else:
            print(df)

    methods = {
        'update': update_config_files,
        'delete': delete_all_created_configs,
        'get_repo': get_algo_config_repo,
        'get_files': get_config_files,
        'pick': pick_config_file,
        'view': view_config_file,
        'get_df_view': get_df_view,
    }
    return methods[method]()


def pull_df_from_html(filepath):
    with open(filepath, 'r') as file:
        text = file.read()

    df = pd.read_html(text)[0]

    columns = []
    for name in df.columns:
        n = name[0]
        if name[0].startswith('Unnamed'):
            n = name[1]
        columns.append(n)

    df.columns = columns
    return df



# region Unused
def csv_to_dict(file_path):
    # region Docstring
    '''
    # CSV to Dictionary
    Converts 

    ## Parameters:{
    ####    `param`:
    ## }

    ## Process:

    ### 1)

    ## Notes:
    - Notes

    ## TO DO:
    - Item
    '''
    # endregion Docstring
    df = pd.read_csv(file_path)
    df = df.set_index('type')
    df = df[['value']]
    dictionary = df.to_dict()['value']
    return dictionary
# endregion Unused
