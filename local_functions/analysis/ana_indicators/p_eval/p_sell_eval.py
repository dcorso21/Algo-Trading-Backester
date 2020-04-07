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
        gl.s_conds.exposure_over_account_limit
    ]

    for func in sell_conds:
        sells = func()
        if len(sells) != 0:
            break

    return sells
