from local_functions.analysis.ana_indicators.d_eval import d_update_docs
from local_functions.analysis.ana_indicators.d_eval import d_price_eval

import pandas as pd
import logging

def run_daily(current, current_frame):

    p_eval = d_price_eval.pricing_eval(current,current_frame)
    
    if len(current_frame) >= 5:
        v_eval = volume_eval(current,current_frame)

    d_update_docs.update_files(current,current_frame)

    #If both true, return True for the go ahead to buy. 
    if p_eval:# and v_eval:
        return True
    
    
def volume_eval(current,current_frame):
    binary = volume_min_check(current_frame, mins_back = 5, minimum_volume= 100000)
    return binary

def volume_min_check(current_frame, mins_back, minimum_volume):
    df = current_frame.tail(mins_back)
    
    # drop current row... 
    df = df.head(mins_back-1)
    
    vols = list(df.volume)
    closes = list(df.close)
    
    dvol = []
    
    for close, vol in zip(closes,vols):
        
        close = float(close)
        vol = float(vol)
        
        dvol.append(close*int(float(vol)))
    

    dvol = sorted(dvol)
    
    if dvol[0] > minimum_volume:
        trade = True
    else:
        trade = False
    return trade

def update_movement(df):
    
    df['red_green'] = red_green(df[0],df[3])
    df['volatility'] = get_volatility(df[1],df[2])
    df['avg_vola'] = df.volatility.rolling(5).mean()

    df.to_csv('temp_assets/daily.csv')

def run_momentum(current_frame):
    
    run_list = []
    run = 0
    
    vola_list = []
    
    hs = [0]
    ls = [0]
    
    rel_to_open = []
    
    for row in range(0, len(current_frame)):
        minute = list(current_frame.iloc[row])
        o,h,l,c = minute[2],minute[3],minute[4],minute[5]
        v = minute[6]
    
        if c > o:
            if run < 0:
                run = 1
                ls.append(l)
            else:  
                run += 1
        elif c < o: 
            if run > 0:
                run = -1
                hs.append(h)
            else:
                run += -1
        
        run_list.append(run)

        if run > 1:
            hs.append(h)
        
        if run < 1: 
            ls.append(l)
        
        if (run == 1):
            vola_list.append(get_volatility([h],[l])[0])
            ls.append(l)
        elif (run == -1):
            vola_list.append(get_volatility([h],[l])[0])
            hs.append(h)
        else:
            vola_list.append(get_volatility([hs[-1]],[ls[-1]])[0])
            
        rel_to_open.append(open_to_price(current_frame, c))
        
    momentum_frame = pd.DataFrame({'run':run_list,'run_vola':vola_list,'rel_open':rel_to_open})
    
    return momentum_frame
    
def ana_momentum(momentum_frame, current_frame):
    df = momentum_frame
    df['vola'] = get_volatility(current_frame.high, current_frame.low)
    df['avg_vola'] = df.vola.rolling(window = 5).mean()
    mean_vola = df.vola.mean()
    
    cond1 = list(df.run)[-1] < -2
    
    cond2 = list(df.vola)[0] > 2 * list(df.avg_vola)[0]
    
    cond3 = list(df.run_vola)[0] > mean_vola
    
    if cond1 and cond2: # and cond3:
        Buy = True
    else: 
        Buy = False
    
    return Buy
    
