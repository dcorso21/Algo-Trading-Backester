from local_functions.main import global_vars as gl


def analyse():

    # If feedback is false, dont run the function, return the blank df...
    if gl.loop_feedback == False:
        # gl.logging.info('build orders skip')
        return gl.pd.DataFrame()

    # Analyse Daily Movement
    gl.daily_ana.run_daily()

    # Build Orders
    orders = gl.position_ana.build_orders()

    return orders
