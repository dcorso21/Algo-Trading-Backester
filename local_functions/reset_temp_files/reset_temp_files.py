def temp_files():

    import pandas as pd
    import json
    import logging

    # PL JSON:
    # managed here
    pls = {
        'pl_unreal': 0,
        'pl_real': 0,
        'last_ex': 0,
        'max_ex': 0
           }
    json_file = json.dumps(pls)
    f = open('temp_assets/pl_open_closed.json', 'w')
    f.write(json_file)
    f.close()

    # daily_ana
    # managed in the daily_eval file
    daily_eval = pd.DataFrame()
    daily_eval.to_csv('temp_assets/analysis/daily_eval.csv')

    # d_vol_json
    # managed here
    volas = {
        'current': 'nan', 
        'three_min': 'nan',
        'five_min': 'nan',
        'ten_min': 'nan',
        'mean': 'nan'
             }

    json_file = json.dumps(volas)
    f = open('temp_assets/analysis/volas.json', 'w')
    f.write(json_file)
    f.close()

    # yearly_ana
    # managed in the yearly_eval file
    yearly_eval = pd.DataFrame()
    yearly_eval.to_csv('temp_assets/analysis/yearly_eval.csv')

    # daily
    # in the main outline
    daily = pd.DataFrame()
    daily.to_csv('temp_assets/charts/daily.csv')

    # positions
    # managed in the positions_ana file
    filled_orders = pd.DataFrame()
    filled_orders.to_csv('temp_assets/all_orders/filled_orders.csv')

    # positions
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
