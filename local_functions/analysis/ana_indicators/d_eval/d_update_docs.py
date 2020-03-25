from local_functions.main import global_vars as gl


def update_files():

    if gl.current()['second'] == 59:
        gl.vf.update_volas()
        gl.mom.update_momentum()

        if len(gl.mom_frame()) != 0:

            # in the future, make a condition to only update if outside the current support resistance
            gl.sup_res.update_supports_resistances()
