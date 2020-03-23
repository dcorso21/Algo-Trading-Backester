from local_functions.trade_funcs import sim_executions as sim_exe

import pandas as pd
import logging
import json

'''
Purpose of this sheet:

1. Update Fills

2. Update Real PL

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
    # logging.info('orders still awaiting fill: {}'.format(len(open_orders)))
    
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
    current_positions, realized = get_current_positions(current_positions)
    
    # add some columns for return and PL
    current_positions = append_return_and_pl(current, current_positions)
    
    # if there are open orders, then calculate the unrealized pl
    if len(current_positions) > 0:
        unreal = current_positions.un_pl.sum()
    else:
        unreal = 0
    
    pls = pull_json('temp_assets/pl_open_closed.json')
    real = pls['pl_real']
    real += realized
    return real, unreal
            
def update_pl(real, unreal):
    
    pls = pull_json('temp_assets/pl_open_closed.json')
    
    if real != 'skip':
        pls['pl_real'] = real
    
    if unreal != 'skip':
        pls['pl_unreal'] = unreal
        
        
    save_json(pls,'temp_assets/pl_open_closed.json')
    

def get_current_positions(positions):
    '''
    Takes a DF of filled orders and filters out the orders no longer active (current) by looking at the sells. 

    '''
    if len(positions) == 0:
        return pd.DataFrame()
    else: 
        columns = ['ticker','exe_time','send_time','buy_or_sell','cash','qty','exe_price']
        df = positions[columns]
        
        # current = pull_json('temp_assets/current_ohlcvs.json')
        
        buys = df[df['buy_or_sell'] == 'BUY']
        sells = df[df['buy_or_sell'] == 'SELL']
        realized = 0

        for qty, price in zip(sells.qty, sells.exe_price):
            remainder = qty
            while remainder > 0:

                first_row = buys.index.tolist()[0]

                # open_orders.reset_index()

                # if there are more shares sold than the one row
                # calculate the remainder and drop the first row...
                if (buys.at[first_row, 'qty'] - remainder) <= 0:
                    realized += (price - buys.at[first_row, 'exe_price']) * buys.at[first_row, 'qty']
                    diff = int(remainder - buys.at[first_row, 'qty'])
                    buys = buys.drop(first_row)
                    # I use this workaround because the loop is based on this value
                    # If the value happens to be zero, the loop will break. 
                    remainder = diff

                # if the shares sold are not greater than the row's qty
                # calculate the new row's value, stop the loop... 
                elif (buys.at[first_row, 'qty'] - remainder) > 0:
                    realized += (price - buys.at[first_row, 'exe_price']) * remainder
                    buys.at[first_row, 'qty'] = buys.at[first_row, 'qty'] - remainder
                    remainder = 0

        buys.to_csv('temp_assets/all_orders/current_positions.csv')
        #logging.info('PA: refreshed current_positions')
        return buys, realized

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