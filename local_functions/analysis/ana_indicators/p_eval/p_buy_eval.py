from local_functions.main import global_vars as gl


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
    if bad_buy_conditions():
        return gl.pd.DataFrame()

    # 1. Check to see if there are any current_positions.
    # If there aren't any current_positions, ---> return a starting position buy DF.
    if len(gl.current_positions) == 0:
        return gl.b_conds.starting_position()

    buy_conds = [
        gl.b_conds.drop_below_average
    ]

    # 2. Go through each Buy Condition to see if the time is right to sell (this second)
    # Order is important as the first function to yield an order will break the loop and return the DF.
    for func in buy_conds:
        buys = func()
        if len(buys) != 0:
            break

    return buys


def bad_buy_conditions():
    '''
    ## Look for Bad Buy Conditions
    Checks conditions to see if stock is worth buying (this second).

    Returns True or False -  True meaning that the conditions ARE BAD.

    ### Conditions: (Don't run the code if BOTH conditions are met.)
    #### 1) If the chart looks bad 
    Specifically, if the global chart_response variable == False.
    #### 2) If there are no current positions. 
    '''
    # DONT RUN THE CODE IF THESE CONDITIONS ARE MET.
    # 1) If the chart looks bad
    cond1 = (gl.chart_response == False)
    # 2) If there are no current positions.
    cond2 = (len(gl.current_positions) != 0)
    if cond1 and cond2:
        return True
    return False
