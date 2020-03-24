from local_functions.analysis.ana_indicators import common
from local_functions.main import global_vars as gl

import pandas as pd
import json
import logging


def update_volas():

    cf = gl.current_frame

    # make volatility column
    cf['vola'] = common.get_volatility(
        cf['high'], cf['low'])

    # calculate volatilities for different time increments
    cf['three_vola'] = cf.vola.rolling(3).mean()
    cf['five_vola'] = cf.vola.rolling(5).mean()
    cf['ten_vola'] = cf.vola.rolling(10).mean()
    volas = {
        'current': cf['vola'].tolist()[-1],
        'mean': cf.vola.mean(),
        'three_min': cf['three_vola'].tolist()[-1],
        'five_min': cf['five_vola'].tolist()[-1],
        'ten_min': cf['ten_vola'].tolist()[-1]
    }

    # save json file
    common.save_dict_to_csv(volas, r'temp_assets/analysis/volas.json')
