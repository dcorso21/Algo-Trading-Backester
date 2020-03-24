from local_functions.pull_historical import historical_funcs as hist
import pandas as pd


def get_volas():
    df = pd.read_csv(r'temp_assets\analysis\volas.csv')
    df = df.set_index('type')
    df = df[['value']]
    volas = df.to_dict()['value']
    return volas


def get_pl_ex():
    df = pd.read_csv(r'temp_assets\pl_and_ex.csv')
    df = df.set_index('type')
    df = df[['value']]
    pl_ex = df.to_dict()['value']
    return pl_ex


def get_current():
    df = pd.read_csv(r'temp_assets\pl_and_ex.csv')
    df = df.set_index('type')
    df = df[['value']]
    current = df.to_dict()['value']
    return current


# Loop Variables


pos_update = False


loop_feedback = True

# response if chart looks like a good time to trade. Managed in daily_ana
chart_response = False


# Sim Data
sim_df = hist.get_mkt_data(r'example.csv')

# Referenced CSVs

current_frame = pd.read_csv(r'temp_assets\charts\daily.csv')

# Orders
open_orders = pd.read_csv(r'temp_assets\all_orders\open_orders.csv')
current_positions = pd.read_csv(
    r'temp_assets\all_orders\current_positions.csv')
filled_orders = pd.read_csv(r'temp_assets\all_orders\filled_orders.csv')

# Analysis
mom_frame = pd.read_csv(r'temp_assets\analysis\daily_eval.csv')
sup_and_res = pd.read_csv(r'temp_assets\analysis\supports_resistances.csv')
yearly_frame = pd.read_csv(r'temp_assets\analysis\yearly_eval.csv')

# Dictionaries

current = get_current()


pl_ex = get_pl_ex()

volas = get_volas()
