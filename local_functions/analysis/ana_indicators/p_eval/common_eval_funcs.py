import datetime
import pandas as pd
import json
import logging

def cash_to_shares(cash,price):
    
    return (int(cash/price), round(price,3))

def get_timestamp(minute,second):

    from datetime import datetime, timedelta
    time = datetime.strptime(minute, '%H:%M:%S')
    time = time+timedelta(seconds=second)
    return time.strftime('%H:%M:%S')

def get_average(current_positions):
    
    df = current_positions
    avg = df.cash.sum() / df.qty.sum()
    return avg
            
def get_exposure(current_positions):
    
    df = current_positions
    ex = df.cash.sum()
    
    pls = pull_json('temp_assets/pl_open_closed.json')
    
    pls['last_ex'] = ex
    if pls['max_ex'] < ex:
        pls['max_ex'] = ex
        
    
    save_json(pls, 'temp_assets/pl_open_closed.json')
    
    return ex, pls

def pull_json(filename):

    json_file = open(filename)
    dictionary = json.load(json_file)
    return dictionary

def save_json(dictionary, filename):
    
    json_file = json.dumps(dictionary)
    with open(filename,'w'):
        pass
    f = open(filename,'w')
    f.write(json_file)
    f.close()
    
def get_open_orders():
    
    open_orders = pd.read_csv('temp_assets/all_orders/open_orders.csv')
    
    return open_orders
