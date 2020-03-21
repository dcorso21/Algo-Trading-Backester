from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common
from local_functions.analysis.ana_indicators.p_eval import order_creators as create


import pandas as pd
import json
import logging

def buy_eval(current_positions,current,current_frame, open_orders):
    
    if len(open_orders) == 0:
    
        if len(current_positions) == 0:                      
            buys = create.create_buys(250, current, current_frame)
        else: 

            avg = common.get_average(current_positions)
            ex, pls = common.get_exposure(current_positions)
            # should be a function for calculating buy amount
            
            volas = common.pull_json('temp_assets/analysis/volas.json')
            
            volas_list = list(volas.values())
            # get rid of nan values as you can't get max with 
            volas_cleaned = [x for x in volas_list if str(x) != 'nan']
            
            if len(volas_cleaned) == 0:
                drop_percent = 1 - ((current['high'] - current['low'])/current['low'])
            else:
                drop_percent = (100 - max(list(map(int,volas_cleaned))))*.01
            
            if current['close'] < (avg * drop_percent):
                trade =True
            else:
                buys = pd.DataFrame()
                trade = False

            if trade == True:
                buys = create.create_buys(ex, current, current_frame)
            else:
                buys = pd.DataFrame()
                
    else:
        buys = pd.DataFrame()

    return buys

