from local_functions.main import global_vars as gl


def sell_eval():
    if len(gl.open_orders()) != 0 or (len(gl.current_positions()) == 0):
        return gl.pd.DataFrame()

    feedback = True
    loop = True

    while loop:

        sells, loop = gl.s_conds.eleven_oclock_exit()
        sells, loop = gl.s_conds.three_perc_gain()
        sells, loop = gl.s_conds.target_unreal(50)
        sells, loop = gl.s_conds.exposure_over_account_limit()

        loop = False

    return sells
