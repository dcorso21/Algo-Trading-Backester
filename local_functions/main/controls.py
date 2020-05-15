from local_functions.analyse import order_eval
from local_functions.main import global_vars as gl

# For configuration of settings.
# in the case of deprecation, setting False will keep the old settings.
lock_defaults = True

'''----- Misc -----'''
misc = {
    'hard_stop': '10:30:00',
    'dollar_risk': -500,
    'ideal_volatility': 3,
}


'''----- ORDER CONDITIONS -----'''
# region Default Params for Sell Conditions
'''----- SELL CONDITIONS-----'''
# sc = order_eval.sell_conditions

# region Dollar Risk Check
dollar_risk_check = {
    'active': True,
    'priority': 1,
}
# endregion Dollar Risk Check

# region Timed Exit
stop_time = gl.pd.to_datetime(misc['hard_stop'])
stop_time = stop_time - gl.datetime.timedelta(minutes=2)
stop_time = stop_time.strftime('%H:%M:%S')

timed_exit = {
    'active': True,
    'priority': 2,
    'time': stop_time,
}
# endregion Timed Exit

# region Exposure Over Account Limit
exposure_over_account_limit = {
    'active': True,
    'priority': 3,
}
# endregion Exposure Over Account Limit

# region Percentage Gain
percentage_gain = {
    'active': True,
    'priority': 4,
    'perc_gain': 3
}
# endregion Percentage Gain

# region Target Unreal
# sc.target_unreal
target_unreal = {
    'active': True,
    'priority': 5,
    'target_unreal': 20
}
# endregion Target Unreal

sell_cond_params = {
    'dollar_risk_check': dollar_risk_check,
    'timed_exit': timed_exit,
    'exposure_over_account_limit': exposure_over_account_limit,
    'percentage_gain': percentage_gain,
    'target_unreal': target_unreal,
}

sell_conditions = []

# endregion Default Params for Sell Conditions


# region Default Params for Buy Conditions

# region drop below average
drop_below_average = {
    'active': True,
    'priority': 1,
    'min_vola': 2.5,
    'max_vola': 5
}
# endregion drop below average

# region aggressive average
aggresive_average = {
    'active': False,
    'priority': 2,
}
# endregion aggressive average


buy_cond_params = {
    'aggresive_average': aggresive_average,
    'drop_below_average': drop_below_average,
}

buy_conditions = []

# endregion Default Params for Buy Conditions


def set_sell_conditions():
    global sell_conditions
    sp = sell_cond_params
    active = [(sp[cond]['priority'], cond)
              for cond in sp.keys() if sp[cond]['active'] == True]
    sell_conditions = [entry[1] for entry in sorted(active)]


def set_buy_conditions():
    global buy_conditions
    bp = buy_cond_params
    active = [(bp[cond]['priority'], cond)
              for cond in bp.keys() if bp[cond]['active'] == True]
    buy_conditions = [entry[1] for entry in sorted(active)]


def reset_variables(mode, csv_file):
    '''
    ## Reset Variables
    There are many global variables that are used throughout the algorithm, 
    and this file resets them so you can easily run the algo back to back. 
    '''

    def get_sim_df(csv_file):
        m = gl.pd.read_csv(csv_file)
        m['open'] = m.open.astype(float)
        m['high'] = m.high.astype(float)
        m['low'] = m.low.astype(float)
        m['close'] = m.close.astype(float)
        m['volume'] = m.volume.astype(float).astype(int)
        # Re-Order
        m = m[['ticker', 'time', 'open', 'high', 'low', 'close', 'volume']]
        return m

    if mode == 'csv':
        gl.csv_indexes = []
        gl.sim_df = get_sim_df(csv_file)
        gl.csv_name = gl.os.path.basename(csv_file).strip('.csv')

    gl.order_count = 0

    gl.pos_update = False
    gl.loop_feedback = True
    gl.buy_lock = False
    gl.sell_out = False
    gl.chart_response = False

    gl.order_specs = gl.pd.DataFrame()
    gl.queued_orders = gl.pd.DataFrame()
    gl.open_orders = gl.pd.DataFrame()
    gl.cancelled_orders = gl.pd.DataFrame()
    gl.open_cancels = {}

    gl.current_positions = gl.pd.DataFrame()
    gl.filled_orders = gl.pd.DataFrame()
    gl.current_frame = gl.pd.DataFrame()
    gl.mom_frame = gl.pd.DataFrame()
    gl.sup_res_frame = gl.pd.DataFrame()
    gl.log = gl.pd.DataFrame()

    # PL and Exposure
    gl.sys.dont_write_bytecode = True

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

    gl.pl_ex = pl_ex

    # current
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

    # last_current
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

    gl.current = current
    gl.last = last

    # volas
    volas = {
        'differential': 'nan',
        'current': 'nan',
        'three_min': 'nan',
        'five_min': 'nan',
        'ten_min': 'nan',
        'mean': 'nan'
    }

    gl.volas = volas
    # volumes
    volumes = {
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

    gl.volumes = volumes

    # Logging Notes
    # Log is now managed in global vars and log_funcs

    # Logging Efficiency
    # df = gl.pd.DataFrame()
    # headers = gl.pd.Series(
    #     ['minute', 'second', 'function', 'run_time'])

    # df = df.append(headers, ignore_index=True)
    # df = df.set_index(0)
    # df.to_csv(gl.filepath['efficiency_log'], header=False)

    print('variables reset')


def configure_settings(config):
    if config == 'last':
        config = gl.get_config_files()[0]
    elif config == 'pick':
        config = gl.pick_config_file()

    import json
    config = json.loads(config.decoded_content)
    global misc, buy_cond_params, sell_cond_params

    if lock_defaults == True:
        if config['default']['everything']:
            return
        if config['default']['misc'] != True:
            misc = config['master']['misc']
        if config['default']['order_conditions'] != True:
            if config['default']['buy_conditions'] != True:
                buy_cond_params = config['master']['order_conditions']['buy_conditions']
            if config['default']['buy_conditions'] != True:
                buy_cond_params = config['master']['order_conditions']['sell_conditions']
        return 

    misc = config['master']['misc']
    buy_cond_params = config['master']['order_conditions']['buy_conditions']
    sell_cond_params = config['master']['order_conditions']['sell_conditions']
    return 


def master_configure(config, mode, csv_file, batch_path):
    gl.batch_path = batch_path
    reset_variables(mode, csv_file)
    configure_settings(config)
    set_buy_conditions()
    set_sell_conditions()
    print('settings configured')
