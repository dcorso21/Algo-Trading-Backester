from local_functions.analysis.ana_indicators.p_eval import p_sell_eval as p_sell 
from local_functions.analysis.ana_indicators.p_eval import p_buy_eval as p_buy  
from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common

import pandas as pd
import json
import logging

def build_orders(response, current, current_frame, update, open_orders): 

    # accesses the positions csv and the current_positions
    positions, current_positions = retreive_positions(current, update)

    # return a df of sell orders, or a blank df as well as a decision to keep trading past this minute. 
    sell_orders, feedback = p_sell.sell_eval(current_positions,current, current_frame, open_orders)

    # if there are any sell orders, save current_positions to be referenced in trade funcs
    if len(sell_orders) != 0:
        sell_log = 'PA: signal to sell {} shares'.format(sell_orders.qty.sum())
        logging.info(sell_log)
        current_positions.to_csv('temp_assets/all_orders/current_positions.csv')

    # if there is a signal to buy...    
    if response:
        buy_orders = p_buy.buy_eval(current_positions,current, current_frame,open_orders)
        if len(buy_orders) != 0:
            buy_log = 'PA: signal to buy {} shares, cash = {}'.format(buy_orders.qty.sum(), buy_orders.cash.sum())
            logging.info(buy_log)

        all_orders = sell_orders.append(buy_orders, sort = False)

    else:
        all_orders = sell_orders

    # return all orders, even if it just an empty frame...
    return all_orders, feedback


def retreive_positions(current, update):
    
    positions = pd.read_csv('temp_assets/all_orders/filled_orders.csv')
    
    if update:
        current_positions = get_current_positions(positions)
    else:
        current_positions = pd.read_csv('temp_assets/all_orders/current_positions.csv')
        
    if len(current_positions) != 0:
        current_positions = append_return_and_pl(current, current_positions)
        update_pl(False,current_positions.un_pl.sum())
    
    return positions, current_positions
    
   

def get_current_positions(positions):
    
    if len(positions) == 0:
        return pd.DataFrame()
    else: 
        columns = ['ticker','exe_time','send_time','buy_or_sell','cash','qty', 'exe_price']
        df = positions[columns]
        
        # current = pull_json('temp_assets/current_ohlcvs.json')
        
        buys = df[df['buy_or_sell'] == 'BUY']
        sells = df[df['buy_or_sell'] == 'SELL']

        for x in sells.qty:
            remainder = x
            while remainder > 0:

                # if there are more shares sold than the one row
                if (buys.iloc[0:1,5].iloc[0] - remainder) <= 0:
                    remainder = int(remainder - buys.iloc[0:1,5])
                    #drop first row
                    buys = buys.drop(buys.index.tolist()[0])

                # if the shares sold are not greater than the row
                elif (buys.iloc[0:1,5].iloc[0] - remainder) > 0:
                    buys.iloc[0:1,5] = buys.iloc[0:1,5] - remainder
                    remainder = 0

        buys.to_csv('temp_assets/all_orders/current_positions.csv')
        #logging.info('PA: refreshed current_positions')
        return buys

def pull_json(filename):

    json_file = open(filename)
    dictionary = json.load(json_file)
    return dictionary

def save_json(dictionary, filename):
    
    json_file = json.dumps(dictionary)
    with open(filename,'w'):
        pass
    f = open(filename,'w')
    f.write(json_file)
    f.close()
    
def append_return_and_pl(current, current_orders):
    
    ret = []  
    for x in current_orders.exe_price:
        ret.append(round(((current['close'] - x)/x)*100,1))
        
    current_orders['p_return'] = ret
    current_orders['un_pl'] = current_orders.cash*current_orders.p_return*.01
    return current_orders

def update_pl(real, unreal):
    
    pls = pull_json('temp_assets/pl_open_closed.json')
    if real:
        pls['pl_real'] = real
    if unreal:
        pls['pl_unreal'] = unreal
    save_json(pls,'temp_assets/pl_open_closed.json')