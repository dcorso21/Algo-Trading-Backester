from local_functions.analysis.ana_indicators import common
from local_functions.analysis.ana_indicators.d_eval.manage_docs import momentum as mom
from local_functions.analysis.ana_indicators.d_eval.manage_docs import supports_resistances as sup_res
from local_functions.analysis.ana_indicators.d_eval.manage_docs import volas
from local_functions.main import global_vars as gl


import pandas as pd
import json
import logging


def update_files():

    if gl.current['second'] == 59:
        volas.update_volas()
        mom.update_momentum()

        if len(gl.mom_frame) != 0:

            # in the future, make a condition to only update if outside the current support resistance
            sup_res.update_supports_resistances()
