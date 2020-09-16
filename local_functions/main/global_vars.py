# 3rd party
from pathlib import Path
from functools import wraps
import requests
import sys
import shutil
import os
import glob
import random
import logging
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui

import numpy as np
import json
import datetime
import pandas as pd
pd.options.mode.chained_assignment = None


from local_functions.main import log_funcs
from local_functions.plotting import api_chart
from local_functions.plotting import candles
from local_functions.plotting import plot_results as plotr
from local_functions.trade_funcs import trade_funcs
from local_functions.trade_funcs import sim_executions as sim_exe
from local_functions.data_management import historical_funcs as hist
from local_functions.data_management import stock_screening as screen
from local_functions.data_management import gather_data as gather
from local_functions.account import account_info as account
from local_functions.analyse import update_docs
from local_functions.main import configure
from local_functions.analyse import order_tools
from local_functions.analyse import order_eval
from local_functions.analyse import common
from local_functions.analyse import analyse
from local_functions.main import algo

# Custom

# endregion imports

directory = Path.cwd()
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
# list the starting strategy
strategy = 'strat_name'
strategy_mode = 'consolidate'
# seconds that momentum is going in the same direction.
# Negative means that the momentum is down
sec_mom = 0
# price, Cents per second
sec_mom_slope = [0,0]


# CSV Trading
batch_dir = ''
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
pl_ex_frame = 'Dataframe'
volume_frame = 'Dataframe'
volas_frame = 'Dataframe'
cancelled_orders = 'Dataframe'
current_positions = 'Dataframe'
filled_orders = 'Dataframe'
current_frame = 'Dataframe'
mom_frame = 'Dataframe'
sup_res_frame = 'Dataframe'
log = 'Dataframe'
tracker = 'Dataframe'
# endregion Frames


current = {
    'open': 'nan',
    'high': 'nan',
    'low': 'nan',
    'close': 'nan',
    'volume': 'nan',
    'second': 'nan',
    'minute': 'nan',
    'ticker': 'nan'
}
last = {
    'open': 'nan',
    'high': 'nan',
    'low': 'nan',
    'close': 'nan',
    'volume': 'nan',
    'second': 'nan',
    'minute': 'nan',
    'ticker': 'nan'
}
pl_ex = {
    'unreal': 0,
    'min_unreal': 0,
    'max_unreal': 0,
    'real': 0,
    'min_real': 0,
    'max_real': 0,
    'last_ex': 0,
    'max_ex': 0
}
volas = {
    'differential': 'nan',
    'current': 'nan',
    'three_min': 'nan',
    'five_min': 'nan',
    'ten_min': 'nan',
    'mean': 'nan'
}
volumes = {
    'fail_check': 'bool',
    'safe_capital_limit': 'nan',
    'differential': 'nan',
    'mean': 'nan',
    'minimum': 'nan',
    'extrap_current': 'nan',
    'three_min_mean': 'nan',
    'three_min_min': 'nan',
    'five_min_mean': 'nan',
    'five_min_min': 'nan',
    'ten_min_mean': 'nan',
    'ten_min_min': 'nan',
}

open_cancels = {}
last_order_check = ['09:30:00', 1, 'price']
close_sup_res = ['closest_support', 'closest_resistance']


class GlobalV:
    def __init__(self):
        self.current = current.copy()
        self.last = last.copy()
        self.pl_ex = pl_ex.copy()
        self.pl_ex_frame = pl_ex_frame.copy()
        self.volas = volas.copy()
        self.volas_frame = volas_frame.copy()
        self.volumes = volumes.copy()
        self.volume_frame = volume_frame.copy()
        self.order_specs = order_specs.copy()
        self.queued_orders = queued_orders.copy()
        self.open_orders = open_orders.copy()
        self.cancelled_orders = cancelled_orders.copy()
        self.current_positions = current_positions.copy()
        self.filled_orders = filled_orders.copy()
        self.current_frame = current_frame.copy()
        self.mom_frame = mom_frame.copy()
        self.sup_res_frame = sup_res_frame.copy()
        self.log = log.copy()
        self.tracker = tracker.copy()


def current_price():
    return current['close']


def save_dict_to_frame(dictionary: dict) -> 'df':
    # region Docstring
    '''
    # Save Dictionary to Frame
    Converts dictionary to DataFrame 

    ## Parameters:{
    ####    `dictionary`: dict to be converted 
    ## }
    '''
    # endregion Docstring
    df = pd.DataFrame(dictionary, index=['value']).T
    df = df.reset_index().rename(columns={'index': 'type'})
    return df


def save_frame(df, file_name: str, path_to_file: Path):
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
    index_path = str(batch_dir / 'batch_index.html')

    text = text.replace('^^^doc_name^^^', page_names[file_name])
    text = text.replace('^^^csv_name^^^', csv_name)
    text = text.replace('^^^asset_path^^^', asset_path)
    text = text.replace('^^^index_path^^^', index_path)
    text = text.replace('<!-- table_insert -->', table)

    dst = path_to_file / f'{file_name}.html'

    with open(dst, 'x') as file:
        file.write(text)


def clear_all_in_folder(folder: str, confirm=False, print_complete=False, delete_dir=False):
    # region Docstring
    '''
    # Clear All in Folder
    Clear all files in given folder 

    #### Returns nothing, clears folder.

    ## Parameters:{
    ####    `folder`: name of folder
    ####    `confirm`: ask before deleting contents
    ####    `print_complete`: notify files have been deleted with a print statement.  
    ## }
    '''
    # endregion Docstring
    if confirm:
        msg = f'Are you SURE you would like to clear all contents of "{folder}"?   Y/N'
        response = input(msg)
        if response.upper() != 'Y':
            print('function cancelled, nothing deleted')
            return

    import os
    import shutil
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

    if print_complete:
        print(f'\ncleared contents of directory: "{folder}"')

    if delete_dir:
        try:
            shutil.rmtree(folder)
            if print_complete:
                print(f'\nfolder has been deleted: "{folder}"')
        except Exception as e:
            print(f'Failed to delete {folder}. Reason: {e}')


def save_config(path_to_file):
    # region Docstring
    '''
    # Save Config
    saves config.json used for trading in the temp_assets

    #### Returns nothing, saves the json file. 

    '''
    # endregion Docstring
    global config

    config = json.dumps(config, indent=2)

    path = path_to_file / 'config.json'
    with open(path, 'x') as f:
        f.write(config)

    config = 'default'


def save_all(path_to_folder):
    '''
    ### Save All Files
    Once trading is done, save all global variables to appropriate dir.
    '''
    extend_current_frame()
    # files = {

    #     'current': current,
    #     'pl_ex': pl_ex,
    #     'volas': volas,
    #     'volumes': volumes,

    #     'current_frame': current_frame,
    #     'mom_frame': mom_frame,
    #     'sup_res_frame': sup_res_frame,

    #     'order_specs': order_specs,
    #     'queued_orders': queued_orders,
    #     'cancelled_orders': cancelled_orders,
    #     'open_orders': open_orders,
    #     'current_positions': current_positions,
    #     'filled_orders': filled_orders,

    #     'log': log,

    # }

    if not os.path.exists(path_to_folder):
        os.makedirs(path_to_folder)

    if batch_dir == '':
        save_config(path_to_folder)

    # for file_name, file in zip(files.keys(), files.values()):

    #     if type(file) == dict:
    #         file = save_dict_to_frame(file)

    #     save_frame(file, file_name, path_to_folder)

    # if len(mom_frame) != 0:
    #     # update_docs.update_momentum()
    #     plotr.plot_momentum(mom_frame, current_frame,
    #                         path_to_folder, batch_dir, csv_name)
    # if len(filled_orders) != 0:
    #     plotr.plot_results(current_frame=current_frame,
    #                        filled_orders=filled_orders,
    #                        batch_path=batch_dir,
    #                        directory=path_to_folder,
    #                        csv_name=csv_name)
    debug_plot(path_to_folder=path_to_folder,
               batch_path=batch_dir,
               csv_name=csv_name,
               show=False)


def debug_plot(path_to_folder=None, batch_path=None, csv_name=None, show=True):
    extend_current_frame()
    plotr.deep_tracking_plot(gv=GlobalV(),
                             path_to_folder=path_to_folder,
                             batch_path=batch_path,
                             csv_name=csv_name,
                             show=show)


def custom_traceback(orig_func):
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
            colored_traceback(trace)
            debug_plot()
    return wrapper


def colored_traceback(trace):

    lines = trace.split('\n')
    tracenotice = lines.pop(0)
    empty = lines.pop(-1)
    reason = lines.pop(-1)
    lines.reverse()

    file_info = lines[1::2]
    code_info = lines[::2]

    print('\n', color_format(reason, 'red'), '\n')
    for fi, ci in zip(file_info, code_info):
        print(color_format(ci, 'yellow'))
        print(color_format(fi, 'cyan'))


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


def isnotebook() -> bool:
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


def frame_to_html(df, df_name) -> str:
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


def get_downloaded_configs() -> list:
    # region Docstring
    '''
    # Get Downloaded Configurations
    gets config.json files from the `Downloads/` folder

    #### Returns list of configs

    ## Parameters:{
    ####    `param`:
    ## }
    '''
    # endregion Docstring
    downloads = Path.home() / 'Downloads'
    json_files = glob.glob(str(downloads / '*.json'))
    saved_path = Path.cwd()/'config'/'saved_configurations'
    saved = glob.glob(str(saved_path / '*.json'))
    saved = [os.path.basename(f) for f in saved]

    for config in json_files:
        name = os.path.basename(config)
        if name not in saved:
            shutil.copyfile(config, str(saved_path / name))
            print(f'config {name} imported')

    configs = list(glob.glob(str(saved_path / '*.json')))
    configs.reverse()

    return configs


def show_available_configurations():
    # region Docstring
    '''
    # Show Available Configurations
    gets all available config.json files and displays in a DF

    #### Returns nothing, prints table.
    '''
    # endregion Docstring

    configs = get_downloaded_configs()

    dates, names = [], []
    for config in configs:
        filename = os.path.basename(config)
        date, name = filename.replace('_', '/', 2).split('_', 1)
        name = name.rstrip('.json').replace('_', ' ').title()
        names.append(name)
        dates.append(date)

    frame = {
        'date': dates,
        'name': names,
    }

    df = pd.DataFrame(frame)
    df = df.reset_index(drop=True)

    if isnotebook():
        display(df)
    else:
        print(df)


def pick_config_file() -> str:
    # region Docstring
    '''
    # Pick Config File
    Allows user to choose which config to use in testing. 

    #### Returns filepath of config file.
    '''
    # endregion Docstring
    show_available_configurations()
    prompt = 'input the number which corresponds with the desired configuration. -1 for default'
    response = input(prompt)
    if response == '-1':
        return 'default'
    else:
        return get_downloaded_configs()[int(response)]


def extend_current_frame(mins=10):
    global current_frame
    current_frame = current_frame.reset_index(drop=True)
    mins = min([mins, len(current_frame)])
    last_ind = current_frame.index.to_list()[-1]
    current_frame = sim_df.iloc[0:last_ind+mins]
    return


def pull_df_from_html(filepath) -> 'df':
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


def most_recent_results():
    path = Path.cwd() / 'results'
    for dir, folder, file in os.walk(path):
        break
    x = [i for i in sorted(folder) if i != 'comparison'][-1]
    path = path / x
    for dir, folder, file in os.walk(path):
        break
    x = sorted([(int(i.split('_')[1]), i)
                for i in folder if i != 'comparison'])
    x = x[-1][-1]
    path = path / x
    full_path = (path / 'batch_index.html')
    return pull_df_from_html(full_path)


def save_worst_performers():
    df = most_recent_results()

    df['net'] = df.real_pl + df.unreal_pl
    worst_performers = df.sort_values(
        by='net', ascending=True).head(10).tick_date.to_list()

    def fill_out_filepath(path):
        path = path[0:-2]
        print(path)
        return f'mkt_csvs/{path}.csv'

    worst_performers = [fill_out_filepath(i) for i in worst_performers]
    save_stocklist_to_batchcsvs(worst_performers)
    print('Worst Performers Saved')


def save_stocklist_to_batchcsvs(list_of_csvs):
    list_of_csvs = json.dumps(list_of_csvs, indent=2)
    path = Path.cwd() / 'results' / 'batch_csvs.json'

    with open(path, 'w') as f:
        f.write(list_of_csvs)
        f.close()


def clear_output(num_of_lines):
    # region Docstring
    '''
    # Clear Output
    Clears Print Output of the number of lines passed

    #### Returns nothing.   

    ## Parameters:{
    ####    `num_of_lines`: number of lines to clear
    ## }
    '''
    # endregion Docstring
    # if configure.cut_prints == False:
    #     return
    # elif isnotebook:
    #     return
    import sys
    cursor_up = '\x1b[1A'
    erase_line = '\x1b[2K'
    for _ in range(num_of_lines):
        sys.stdout.write(erase_line)
        sys.stdout.write(cursor_up)
        sys.stdout.write(erase_line)

    sys.stdout.write(cursor_up)
    sys.stdout.write('\r')


def color_format(msg, color):
    # region Docstring
    '''
    # Color Format
    formats print output with color.    

    #### Returns message now wrapped in ANSI color codes. 

    ## Parameters:{
    ####    `msg`: message to be printed. 
    ####    `color`: desired color. 
    ## }
    '''
    # endregion Docstring

    def prRed(msg): return("\033[91m {}\033[00m" .format(msg))
    def prGreen(msg): return("\033[92m {}\033[00m" .format(msg))
    def prYellow(msg): return("\033[93m {}\033[00m" .format(msg))
    def prLightPurple(msg): return("\033[94m {}\033[00m" .format(msg))
    def prPurple(msg): return("\033[95m {}\033[00m" .format(msg))
    def prCyan(msg): return("\033[96m {}\033[00m" .format(msg))
    def prLightGray(msg): return("\033[97m {}\033[00m" .format(msg))
    def prBlack(msg): return("\033[98m {}\033[00m" .format(msg))
    colors = {
        'red': prRed,
        'green': prGreen,
        'yellow': prYellow,
        'light_purple': prLightPurple,
        'purple': prPurple,
        'cyan': prCyan,
    }
    return colors[color](msg)


def tab_df(df):
    from tabulate import tabulate
    if type(df) == dict:
        df = json.dumps(df, indent=2)
        print(df)
        return
    tablefmt = 'fancy_grid'
    print(tabulate(df, headers=df.columns, tablefmt=tablefmt))

# region Unused

# filepath = {
#     'current': r'temp_assets\current.csv',
#     'pl_ex': r'temp_assets\pl_and_ex.csv',
#     'volas': r'temp_assets\volas.csv',
#     'current_frame': r'temp_assets\current_frame.csv',
#     'mom_frame': r'temp_assets\mom_frame.csv',
#     'sup_res_frame': r'temp_assets\supports_resistances.csv',
#     'current_positions': r'temp_assets\current_positions.csv',
#     'filled_orders': r'temp_assets\filled_orders.csv',
#     'open_orders': r'temp_assets\open_orders.csv',

#     'log': r'temp_assets\log.csv',
#     'efficiency_log': r'temp_assets\efficiency_log.csv',
# }

# def csv_to_dict(file_path):
#     # region Docstring
#     '''
#     # CSV to Dictionary
#     Converts

#     ## Parameters:{
#     ####    `param`:
#     ## }

#     ## Process:

#     ### 1)

#     ## Notes:
#     - Notes

#     ## TO DO:
#     - Item
#     '''
#     # endregion Docstring
#     df = pd.read_csv(file_path)
#     df = df.set_index('type')
#     df = df[['value']]
#     dictionary = df.to_dict()['value']
#     return dictionary


# def update_config_files():
#         # region Docstring
#     '''
#     # Update Config Files
#     Updates the algo_config repo on github, creating a new ipynb, default json, and template
#     for testing based on current control.py settings.

#     #### Returns nothing, saves to github.

#     '''
#     # endregion Docstring
#     from config import ipy_creator
#     path = directory
#     repo = get_algo_config_repo()
#     ipy_creator.update_all(path, repo)


# def delete_all_created_configs():
#     # region Docstring
#     '''
#     # Delete All Created Configs
#     deletes all creates config.json files in github repo

#     #### Returns nothing
#     '''
#     # endregion Docstring
#     repo = get_algo_config_repo()
#     created = repo.get_contents('created')
#     if len(created) != 0:
#         for f in created:
#             commit_msg = f"removed {f}"
#             repo.delete_file(f.path, commit_msg, f.sha, branch="master")
#             print(commit_msg)


# def get_algo_config_repo():
#     # region Docstring
#     '''
#     # Get algo_config repo
#     retrieves the repo object using the pygithub package.

#     #### Returns repo object.

#     note: got an email saying that login with u/p will be deprecated soon.
#     '''
#     # endregion Docstring
#     from github import Github
#     user, pasw = 'dcorso21', 'PFgyMWEVJQnZzu2'
#     g = Github(user, pasw)
#     for repo in g.get_user().get_repos():
#         if str(repo) == 'Repository(full_name="dcorso21/algo_config")':
#             break
#     return repo


# def get_config_files():
#     # region Docstring
#     '''
#     # Get Config Files
#     gets all listed config.json files in repo.

#     #### Returns list of github content files which can be converted to dicts.
#     '''
#     # endregion Docstring
#     repo = get_algo_config_repo()
#     files = list(repo.get_contents('created'))
#     files.reverse()
#     return files


# def pick_config_file():
#     # region Docstring
#     '''
#     # Pick Config File
#     prompts to

#     #### Returns chosen config files

#     '''
#     # endregion Docstring
#     files = get_config_files()
#     get_df_view(files)
#     prompt = 'please specify config by number (for default put -1)'
#     num = int(input(prompt))
#     if num == -1:
#         return 'default'
#     return files[num]


# def view_config_file():
#     from config import ipy_creator
#     c = pick_config_file()
#     if c == 'default':
#         c = ipy_creator.make_default_config_json(path=False)
#     else:
#         c = c.decoded_content
#         c = json.loads(c)
#         c = json.dumps(c, indent=4, sort_keys=True)
#     print(c)


# def make_config_metadata(filename):
#     flist = filename.name.split('created/')[0].split('_', 3)
#     fn = flist[3:][0]
#     if fn == '.json':
#         fn = 'no name'
#     else:
#         fn = fn.split('.json')[0]
#     metadata = {
#         'name': [fn],
#         'date': [flist[0]],
#         'time': [f'{flist[1]} {flist[2]}'],
#     }
#     return metadata


# def get_df_view(files=get_config_files()):
#     df = pd.DataFrame()
#     for f in files:
#         row = make_config_metadata(f)
#         dfx = pd.DataFrame(row)
#         df = df.append(dfx, sort=False)

#     df = df.reset_index(drop=True)
#     if isnotebook():
#         display(df)
#     else:
#         print(df)


# def manage_algo_config_repo(method):
#     # region Docstring
#     '''
#     # Manage algo_config repo
#     group of functions for interacting with the algo_config repo on github.

#     #### Returns depends on method

#     ## Parameters:{
#     ####    `method`: str, relates to function to call:
#     -               `update`: updates the template, default.json and colab.ipynb,
#     -               `delete`: remove all config files from created folder in repo but file
#                             can still be found in commit history,
#     -               `get_repo`: returns github repo object,
#     -               `get_files`: returns list of content objects for each json,
#     -               `pick`: allows user to pick which file they would like to see.

#     ## }
#     '''
#     # endregion Docstring

#     methods = {
#         'update': update_config_files,
#         'delete': delete_all_created_configs,
#         'get_repo': get_algo_config_repo,
#         'get_files': get_config_files,
#         'pick': pick_config_file,
#         'view': view_config_file,
#         'get_df_view': get_df_view,
#     }
#     return methods[method]()


# endregion Unused
