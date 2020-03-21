from local_functions.trade_funcs import sim_executions as sim_exe

import pandas as pd
import logging
import json

'''
Purpose of this sheet:

1. Managing open orders

2. Managing Fills

'''

def exe_orders(orders, current, feedback):

    # CLAUSE FOR STOPPING TRADES 
    if feedback == False:
        if len(orders) != 0:
            orders = orders[orders['buy_or_sell'] == 'SELL']
    
    # SIMULATE EXECUTIONS
    # right now its just simulated. 
    new_fills, open_orders = sim_exe.run_trade_sim(orders, current)

    if len(new_fills) != 0:
    
        # UPDATE PL
        # if there are sell orders, do the math and calculate PL
        if len(new_fills[new_fills['buy_or_sell']=='SELL']) != 0:
            real, unreal = get_real_pl(new_fills)
            update_pl(real,unreal)
            logging.info('TF: realized PL updated: {} unreal : {}'.format(real,unreal))

        # UPDATE FILLED CSV
        filled_orders = get_filled_orders()
        filled_orders = filled_orders.append(new_fills,sort = False)
        filled_orders.to_csv('temp_assets/all_orders/filled_orders.csv')

    # log amount of orders awaiting fills. 
    logging.info('orders still awaiting fill: {}'.format(len(open_orders)))
    
    return open_orders

def get_filled_orders():
    filled_orders = pd.read_csv('temp_assets/all_orders/filled_orders.csv')
    if len(filled_orders) != 0:
        columns = ['ticker','exe_time','send_time','buy_or_sell','cash','qty','exe_price']
        filled_orders = filled_orders[columns]
    return filled_orders

def get_real_pl(orders):
    '''
    Retrieve PL and Exposure info from JSON. 
    '''
    
    # get current json
    current = pull_json('temp_assets/current_ohlcvs.json')
    
    # positions currently held. 
    current_positions = pd.read_csv('temp_assets/all_orders/current_positions.csv')
    # refine positions
    columns = ['ticker','exe_time', 'send_time','buy_or_sell','cash','qty','exe_price']
    current_positions = current_positions[columns]
    
    # recalculate current positions with new fills to calculate new PLs
    current_positions = current_positions.append(orders[orders['buy_or_sell']=='SELL'], sort = False)
    current_positions = get_current_positions(current_positions)
    
    # add some columns for return and PL
    current_positions = append_return_and_pl(current, current_positions)
    
    # if there are open orders, then calculate the unrealized pl
    if len(current_positions) > 0:
        unreal = current_positions.un_pl.sum()
    else:
        unreal = 0
    
    pls = pull_json('temp_assets/pl_open_closed.json')
    old_unreal = pls['pl_unreal']
    real = pls['pl_real']
    real += old_unreal - unreal
    return real, unreal
            
def update_pl(real, unreal):
    
    pls = pull_json('temp_assets/pl_open_closed.json')
    
    if real != 'skip':
        pls['pl_real'] = real
    
    if unreal != 'skip':
        pls['pl_unreal'] = unreal
        
        
    save_json(pls,'temp_assets/pl_open_closed.json')
    

def get_current_positions(positions):
    
    if len(positions) == 0:
        return pd.DataFrame()
    else: 
        columns = ['ticker','exe_time','send_time','buy_or_sell','cash','qty','exe_price']
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
    
def append_return_and_pl(current, current_positions):
    
    ret = []  
    for x in current_positions.exe_price:
        ret.append(round(((current['close'] - x)/x)*100,1))
        
    current_positions['p_return'] = ret
    current_positions['un_pl'] = current_positions.cash*current_positions.p_return*.01
    return current_positions