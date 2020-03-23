from local_functions.analysis.ana_indicators import daily_ana, position_ana, yearly_ana

import pandas as pd

# One of the main functions


def analyse(current, current_frame, update, open_orders):
    '''
    ####################################################    
    IN PROGRESS:
    '''

    # yearly_ana.run_yearly(current_frame,yearly_df)

    response = daily_ana.run_daily(current, current_frame)

    if len(current_frame) > 2:
        orders, feedback = position_ana.build_orders(
            response, current, current_frame, update, open_orders)
    else:
        orders = pd.DataFrame()
        feedback = True

    return orders, feedback

    # at the start of each minute, re-asses the minute chart...
#     if (current['second'] == 0) and (len(daily_df) != 0):
#         update_movement(daily_df)
