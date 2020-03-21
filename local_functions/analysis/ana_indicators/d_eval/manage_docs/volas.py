from local_functions.analysis.ana_indicators import common

import pandas as pd
import json
import logging

def update_volas(current_frame):
    
    # make volatility column
    current_frame['vola'] = common.get_volatility(current_frame['high'],current_frame['low'])
    
    # calculate volatilities for different time increments
    current_frame['three_vola'] = current_frame.vola.rolling(3).mean()
    current_frame['five_vola'] = current_frame.vola.rolling(5).mean()
    current_frame['ten_vola'] = current_frame.vola.rolling(10).mean()
    volas = {
        'current':current_frame['vola'].tolist()[-1],
        'mean':current_frame.vola.mean(),
        'three_min':current_frame['three_vola'].tolist()[-1],
        'five_min':current_frame['five_vola'].tolist()[-1],
        'ten_min':current_frame['ten_vola'].tolist()[-1]
    }
    
    # save json file 
    common.save_json(volas,'temp_assets/analysis/volas.json')
    