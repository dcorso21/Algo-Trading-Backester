from local_functions.main import global_vars as gl


def sell_eval():

    # If nothing to sell, return blank df
    if len(gl.current_positions) == 0:
        return gl.pd.DataFrame()
    loop = True

    sell_conds = [
        gl.s_conds.eleven_oclock_exit,
        gl.s_conds.three_perc_gain,
        gl.s_conds.target_unreal,
        gl.s_conds.exposure_over_account_limit
    ]

    for func in sell_conds:
        sells = func()
        if len(sells) != 0:
            break

    return sells
