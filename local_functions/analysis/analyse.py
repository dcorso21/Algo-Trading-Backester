from local_functions.analysis.ana_indicators import daily_ana, position_ana, yearly_ana
from local_functions.main import global_vars as gl

import pandas as pd

# One of the main functions


def analyse(update):
    '''
    ####################################################    
    IN PROGRESS:
    '''

    # yearly_ana.run_yearly(current_frame,yearly_df)

    daily_ana.run_daily()

    if len(gl.current_frame) > 2:
        orders, feedback = position_ana.build_orders(response, update)
    else:
        orders = pd.DataFrame()
        feedback = True

    return orders, feedback

    # at the start of each minute, re-asses the minute chart...
#     if (current['second'] == 0) and (len(daily_df) != 0):
#         update_movement(daily_df)
