def temp_files():

    import pandas as pd
    import json
    import logging

    import sys

    sys.dont_write_bytecode = True

    # PL JSON:
    # managed here
    pls = {
        'unreal': 0,
        'real': 0,
        'last_ex': 0,
        'max_ex': 0
    }

    pl_frame = pd.DataFrame(pls, index=['value']).T
    pl_frame = pl_frame.reset_index().rename(columns={'index': 'type'})
    pl_frame.to_csv(r'temp_assets\pl_and_ex.csv')

    # current
    current = {
        'open': 'nan',
        'high': 'nan',
        'low': 'nan',
        'close': 'nan',
        'volume': 'nan',
        'second': 'nan',
        'minute': 'nan'
    }

    c_frame = pd.DataFrame(current, index=['value']).T
    c_frame = c_frame.reset_index().rename(columns={'index': 'type'})
    c_frame.to_csv(r'temp_assets\current.csv')

    # d_vol_json
    # managed here
    volas = {
        'current': 'nan',
        'three_min': 'nan',
        'five_min': 'nan',
        'ten_min': 'nan',
        'mean': 'nan'
    }

    volas_frame = pd.DataFrame(volas, index=['value']).T
    volas_frame = volas_frame.reset_index().rename(columns={'index': 'type'})
    volas_frame.to_csv(r'temp_assets\analysis\volas.csv')

    # daily_ana
    # managed in the daily_eval file
    daily_eval = pd.DataFrame()
    daily_eval.to_csv('temp_assets/analysis/daily_eval.csv')

    # yearly_ana
    # managed in the yearly_eval file
    yearly_eval = pd.DataFrame()
    yearly_eval.to_csv('temp_assets/analysis/yearly_eval.csv')

    # current_frame
    current_frame = pd.DataFrame()
    current_frame.to_csv(r'temp_assets/charts/current_frame.csv')

    # filled_orders
    # managed in the positions_ana file
    filled_orders = pd.DataFrame()
    filled_orders.to_csv('temp_assets/all_orders/filled_orders.csv')

    # open_orders
    # managed in the positions_ana file
    open_orders = pd.DataFrame()
    open_orders.to_csv('temp_assets/all_orders/open_orders.csv')

    # current_positions
    # managed in the positions_ana file
    current_positions = pd.DataFrame()
    current_positions.to_csv('temp_assets/all_orders/current_positions.csv')

    # Logging Notes
    with open('temp_assets/algo.log', 'w'):
        pass

    logging.basicConfig(filename='temp_assets/algo.log', level=logging.INFO)
    logging.info('Started\n')
    # mylib.do_something()

    print('files reset')
