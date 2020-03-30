from local_functions.main import global_vars as gl


def update_files():
    '''
    ## Update Daily Analysis Files
    Updates the mom_frame, volas and sup_res_frame global variables. 

    ### Details.

    Volas is updated every second. 

    mom_frame and supports/resistances are updated each minute

    ##### Note: Order does not really matter here. 

    '''

    gl.vf.update_volas()
    if gl.current['second'] == 59:
        gl.mom.update_momentum()
        if len(gl.mom_frame) != 0:
            # in the future, make a condition to only update if outside the current support resistance
            gl.sup_res.update_supports_resistances()
