# Imports - list follows folders
from local_functions.account_info import account_info as account
from local_functions.analysis import analyse as ana
from local_functions.analysis import common_ana

# Daily Analysis
from local_functions.analysis.ana_indicators import daily_ana
from local_functions.analysis.ana_indicators.d_eval import d_price_eval, d_update_docs
from local_functions.analysis.ana_indicators.d_eval.manage_docs import momentum as mom
from local_functions.analysis.ana_indicators.d_eval.manage_docs import supports_resistances as sup_res
from local_functions.analysis.ana_indicators.d_eval.manage_docs import volas as vf

# Position Analysis
from local_functions.analysis.ana_indicators import position_ana
from local_functions.analysis.ana_indicators.p_eval import p_buy_eval, p_sell_eval
from local_functions.analysis.ana_indicators.p_eval import order_tools as o_tools
from local_functions.analysis.ana_indicators.p_eval.conditions import buy_conditions as b_conds
from local_functions.analysis.ana_indicators.p_eval.conditions import sell_conditions as s_conds

# Other
from local_functions.assemble_data import gather_data as gather
from local_functions.main import algo
# from local_functions.plotting import plot_results as plotr
from local_functions.pull_historical import historical_funcs as hist
from local_functions.reset_temp_files import reset_temp_files as reset

from local_functions.trade_funcs import sim_executions as sim_exe
from local_functions.trade_funcs import trade_funcs

# Other
import datetime
import pandas as pd
import logging
import random
import sys


filepath = {

    'current': r'temp_assets\current.csv',
    'pl_ex': r'temp_assets\pl_and_ex.csv',
    'current_frame': r'temp_assets\charts\current_frame.csv',
    'daily_ohlc': r'temp_assets\charts\daily.csv',
    'mom_frame': r'temp_assets\analysis\mom_frame.csv',
    'sup_res_frame': r'temp_assets\analysis\supports_resistances.csv',
    'volas': r'temp_assets\analysis\volas.csv',
    'current_positions': r'temp_assets\all_orders\current_positions.csv',
    'filled_orders': r'temp_assets\all_orders\filled_orders.csv',
    'open_orders': r'temp_assets\all_orders\open_orders.csv'

}


# Loop Variables

pos_update = False

loop_feedback = True

chart_response = False


# Sim Data
# only need to reference this once.
sim_df = hist.get_mkt_data(r'example.csv')

# Referenced CSVs


def current_frame():
    return pd.read_csv(filepath['current_frame'])


def daily_ohlc():
    return pd.read_csv(filepath['daily_ohlc'])


# Orders

def open_orders():

    open_orders = pd.read_csv(filepath['open_orders'])
    if len(open_orders) != 0:
        columns = ['ticker', 'send_time', 'buy_or_sell', 'cash', 'qty',
                   'exe_price', 'price_check', 'vol_start', 'wait_duration']
        open_orders = open_orders[columns]

    return open_orders


def current_positions():
    current_positions = pd.read_csv(filepath['current_positions'])
    if len(current_positions) != 0:
        columns = ['ticker', 'exe_time', 'send_time',
                   'buy_or_sell', 'cash', 'qty', 'exe_price']
        current_positions = current_positions[columns]
    return current_positions


def filled_orders():
    filled_orders = pd.read_csv(filepath['filled_orders'])
    if len(filled_orders) != 0:
        columns = ['ticker', 'exe_time', 'send_time',
                   'buy_or_sell', 'cash', 'qty', 'exe_price']
        filled_orders = filled_orders[columns]
    return filled_orders


# Analysis
def mom_frame():
    return pd.read_csv(filepath['mom_frame'])


def sup_res_frame():
    return pd.read_csv(filepath['sup_res_frame'])


# def yearly_frame():
#     return pd.read_csv(r'temp_assets\analysis\yearly_eval.csv')


# Dictionaries


def csv_to_dict(file_path):
    df = pd.read_csv(file_path)
    df = df.set_index('type')
    df = df[['value']]
    dictionary = df.to_dict()['value']
    return dictionary


def save_dict_to_csv(dictionary, file_path):
    df = pd.DataFrame(dictionary, index=['value']).T
    df = df.reset_index().rename(columns={'index': 'type'})
    df.to_csv(file_path)


def current():
    current = csv_to_dict(filepath['current'])
    current['open'] = float(current['open'])
    current['high'] = float(current['high'])
    current['low'] = float(current['low'])
    current['close'] = float(current['close'])
    current['volume'] = int(float(current['volume']))
    current['second'] = int(float(current['second']))

    return current


def pl_ex():
    pl_ex = csv_to_dict(filepath['pl_ex'])
    for x in pl_ex.keys():
        pl_ex[x] = float(pl_ex[x])
    return pl_ex


def volas():
    volas = csv_to_dict(filepath['volas'])
    for x in volas.keys():
        volas[x] = float(volas[x])
    return volas
