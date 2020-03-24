from local_functions.analysis.ana_indicators.p_eval import common_eval_funcs as common
# from local_functions.analysis.ana_indicators.p_eval import order_creators as create

from local_functions.analysis.ana_indicators.p_eval.conditions import buy_conditions as b_cond

import pandas as pd
import json
import logging


def buy_eval(current_positions, current, current_frame, open_orders):
    '''

    DECIDES WHETHER OR NOT TO TRADE. IF CONDITIONS ARE TRUE, THE LOOP IS BROKEN. 

    '''
    trade = False
    loop = True

    if len(open_orders) == 0:

        while (trade == False) or (loop == True):

            # STARTING POSITION
            if len(current_positions) == 0:

                trade, buys = b_cond.starting_position(current, current_frame)

            # ADDING TO EXISTING POSITIONS
            else:

                # Retrieve useful variables
                avg = common.get_average(current_positions)
                ex, pls = common.get_exposure(current_positions)
                volas = common.pull_json('temp_assets/analysis/volas.json')

                max_vola = common.get_max_vola(volas, current)

                '''
                LIST CONDITIONS HERE...
                 
                Order is important...
                '''

                # 1. returns True if the current price is below average by a certain percentage.
                trade, buys = b_cond.drop_below_average(current, avg, max_vola)

            loop = False

    return buys
