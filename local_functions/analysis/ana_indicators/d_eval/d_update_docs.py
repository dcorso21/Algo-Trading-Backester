from local_functions.main import global_vars as gl


def update_files():
    gl.vf.update_volas()
    if gl.current['second'] == 59:
        gl.mom.update_momentum()
        if len(gl.mom_frame) != 0:
            # in the future, make a condition to only update if outside the current support resistance
            gl.sup_res.update_supports_resistances()
