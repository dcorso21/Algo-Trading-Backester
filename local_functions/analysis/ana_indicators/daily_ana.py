from local_functions.main import global_vars as gl


def run_daily():
    '''
    # Run Daily Analysis
    Updates files and looks for patterns in the daily chart. 

    Updates Global chart_response boolean. 

    ## Process:

    ### 1) Runs update_files function
    Updates momentum, supports, resistances and volatility analysis. 

    ### 2) Evaluates current price info with the pricing_eval function. 

    ### 3) Evaluates current volume info with the volume_eval function. 

    ### 4) Based on these assessments, set the global variable chart_response as True or False. 

    '''

    gl.d_update_docs.update_files()

    p_eval = gl.d_price_eval.pricing_eval()

    if len(gl.current_frame) >= 5:
        v_eval = volume_eval()

    # If both true, return True for the go ahead to buy.
    if p_eval:  # and v_eval:
        gl.chart_response = True


def volume_eval():

    binary = volume_min_check(mins_back=5, minimum_volume=100000)
    return binary


def volume_min_check(mins_back, minimum_volume):
    current_frame = gl.current_frame

    if len(current_frame) < mins_back:
        mins_back = len(current_frame)

    df = current_frame.tail(mins_back)

    # drop current row...
    if len(df) != 0:
        df = df.head(mins_back-1)

    vols = list(df.volume)
    closes = list(df.close)

    dvol = []

    for close, vol in zip(closes, vols):

        close = float(close)
        vol = float(vol)

        dvol.append(close*int(float(vol)))

    dvol = sorted(dvol)

    if dvol[0] > minimum_volume:
        trade = True
    else:
        trade = False
    return trade
