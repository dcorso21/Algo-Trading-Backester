from local_functions.main import global_vars as gl


def analyse():
    '''
    # Core Function: Analyse

    Looks at daily (and eventually yearly chart) and decides whether its a good time to trade. 
    Then uses that info, plus info on current positions to create new orders (if any).

    Returns Orders DataFrame.

    ## Process:

    #### Skip Clause:
    If the global variable loop_feedback is set to false, return a blank df.  

    ### 1) Analyse Daily Chart

    ### 2) Build Orders 
    '''

    # If feedback is false, dont run the function, return the blank df...
    if gl.loop_feedback == False:
        return gl.pd.DataFrame()

    # 1) Analyse Daily Chart
    gl.daily_ana.run_daily()

    # 2) Build Orders
    orders = gl.position_ana.build_orders()

    return orders
