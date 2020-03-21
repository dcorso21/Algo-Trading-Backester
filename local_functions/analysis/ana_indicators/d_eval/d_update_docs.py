from local_functions.analysis.ana_indicators import common
from local_functions.analysis.ana_indicators.d_eval.manage_docs import momentum as mom
from local_functions.analysis.ana_indicators.d_eval.manage_docs import supports_resistances as sup_res
from local_functions.analysis.ana_indicators.d_eval.manage_docs import volas

import pandas as pd
import json
import logging

def update_files(current,current_frame):
    
    
    
    if current['second'] == 59:
        volas.update_volas(current_frame)
        mom.update_momentum(current_frame)
    
        if len(pd.read_csv('temp_assets/analysis/daily_eval.csv')) != 0:
            
            # in the future, make a condition to only update if outside the current support resistance
            sup_res.update_supports_resistances(current, current_frame)

