from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common
from local_functions.analysis.ana_indicators.p_eval import order_creators as create

import pandas as pd
import logging

def sell_eval(current_positions,current,current_frame,open_orders):
    feedback = True
    

    
    if len(open_orders) == 0:
        
        # IF THERE ARE SHARES TO SELL...
        if len(current_positions) != 0:

            avg = common.get_average(current_positions)
            ex, pls = common.get_exposure(current_positions)
            ret = current_positions.p_return 
            
            # def get_all_indicators...

            # sell_conditions...

            # 3 % gain... sell all
            if current['close'] > avg * 1.03:
                # sell all
                everything = current_positions.qty.sum()
                sells = create.create_sells(everything, current, current_frame)

            elif pls['pl_unreal'] > 50:
                # sell all
                everything = current_positions.qty.sum()
                sells = create.create_sells(everything, current, current_frame)

            # if exposure is over 30K... sell half
            elif ex > 30000: 
                half = int(current_positions.qty.sum()/2)
                sells = create.create_sells(half, current, current_frame)

            else: sells = pd.DataFrame()

            if (current['minute']  == '11:00:00'):
                everything = current_positions.qty.sum()
                sells = create.create_sells(everything, current, current_frame)
                feedback = False
                logging.info('PS: Sell to Stop...')


        # IF THERE AREN'T SHARES TO SELL:
        else:
            sells = pd.DataFrame()
    else:
        sells = pd.DataFrame()
        
    return sells, feedback 

def get_open_orders():
    
    open_orders = pd.read_csv('temp_assets/all_orders/open_orders.csv')
    
    return open_orders

