# LOCAL FUNCTIONS ###############
    
from local_functions.account_info import account_info
from local_functions.pull_historical import historical_funcs as hist
from local_functions.assemble_data import gather_data as gather
from local_functions.analysis import analyse as ana
from local_functions.trade_funcs import trade_funcs as trd
from local_functions.reset_temp_files import reset_temp_files as reset

# OTHER MODULES

import random
import pandas as pd
import logging
import sys

def main_algo():

    reset.temp_files()
    
    df = hist.get_mkt_data('example.csv')

    daily_df = pd.DataFrame()
    update = False 
    feedback = True
    open_orders = pd.read_csv('temp_assets/all_orders/open_orders.csv')

    # each minute in df
    for row in range(0, len(df)):

        # first, get second data for fake 'real-time' pricing.
        prices, volumes, ticker, minute = hist.create_second_data(df,row,mode = 'momentum')
        logging.info('  {}'.format(minute))

        sys.stdout.write('\rcurrent minute : {}'.format(minute))
        sys.stdout.flush()

        # each second, update current candle and assess patterns, consider trading. 
        for price, volume, second in zip(prices, volumes, range(0,60)):

            current, current_frame = gather.update_candle(price, volume, ticker, minute, second, daily_df)

            if feedback == True:

                # analyse looks at the info and creates orders to be executed. 
                # returns df of orders, or Boolean False if no orders...
                orders, feedback = ana.analyse(current, current_frame, update, open_orders)


            if (feedback == True) or (len(orders) != 0) or (len(open_orders) != 0):

                if len(orders) != 0 or len(open_orders) != 0:
                    open_orders = trd.exe_orders(orders, current, feedback)
                    update = True
                else: update = False

                orders = pd.DataFrame()

            else:
                pass

        # the candle is added to the rest once the minute is complete.
        daily_df = gather.add_new_minute(current, ticker, minute, daily_df)
        daily_df.to_csv('temp_assets/charts/daily.csv')

        logging.info('minute complete\n')

        if minute == '11:05:00': 
            break

    print('\ndone')