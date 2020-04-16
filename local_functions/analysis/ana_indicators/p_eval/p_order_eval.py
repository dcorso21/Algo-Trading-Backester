from local_functions.main import global_vars as gl


def sell_eval():
    '''
    # Sell Evaluation
    Evaluates whether or not it would be a good time to sell, based on a number of SELL CONDIIONS.

    Returns a DataFrame of Sell Orders

    ## Process:
    #### Skip Clause:
    If there are no current positions, there is nothing to sell ---> return empty DataFrame

    ### 1) List Sell Conditions from 'sell_conditions.py' ORDER IS IMPORTANT
    ### 2) Loop through list of Sell Conditions.
    If a condition is met, it will return a DataFrame with a sell order, and the loop will be broken. 
    return ---> Sells DataFrame
    '''
    # If nothing to sell, return blank df
    if len(gl.current_positions) == 0:
        return gl.pd.DataFrame()

    sell_conds = [
        gl.s_conds.eleven_oclock_exit,
        gl.s_conds.percentage_gain,
        gl.s_conds.target_unreal,
        # gl.s_conds.exposure_over_account_limit
    ]

    for func in sell_conds:
        sells = func()
        if len(sells) != 0:
            break

    return sells


def buy_eval():
    '''
    # Buy Evaluation
    Evaluation conditions for buying stock. 

    Returns a DataFrame of Buy Orders. 

    ## Process:
    #### Skip Clause:
    If There are bad conditions for buying ---> return a blank DF. 

    ### 1. Check to see if there are any current_positions.
    If there aren't any current_positions, ---> return a starting position buy DF.   

    ### 2. Go through each Buy Condition to see if the time is right to sell (this second)
    Order is important as the first function to yield an order will break the loop and return the DF. 
    '''

    # Skip Clause:
    # DONT RUN THE CODE IF THESE CONDITIONS ARE MET.
    # If the chart looks bad
    cond1 = (gl.chart_response == False)
    # If there are no current positions.
    cond2 = (len(gl.current_positions) == 0)
    bad_conditions = False
    if cond1 and cond2:
        bad_conditions = True
    if bad_conditions:
        return gl.pd.DataFrame()

    # 1. Check to see if there are any current_positions.
    # If there aren't any current_positions, ---> return a starting position buy DF.
    if len(gl.current_positions) == 0:
        return gl.b_conds.starting_position()

    buy_conds = [
        gl.b_conds.aggresive_average,
        # gl.b_conds.drop_below_average,
    ]

    # 2. Go through each Buy Condition to see if the time is right to sell (this second)
    # Order is important as the first function to yield an order will break the loop and return the DF.
    for func in buy_conds:
        buys = func()
        if len(buys) != 0:
            break

    return buys
