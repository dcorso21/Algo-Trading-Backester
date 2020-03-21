import json

def get_volatility(high_list, low_list):
    vola = []
    for high, low in zip(high_list, low_list):
        vola.append(round(((high - low)/low)*100,1))
    return vola

def save_json(dictionary, filename):
    
    json_file = json.dumps(dictionary)
    with open(filename,'w'):
        pass
    f = open(filename,'w')
    f.write(json_file)
    f.close()
    
def pull_json(filename):

    json_file = open(filename)
    dictionary = json.load(json_file)
    return dictionary

def red_green(current_frame):
    r_g = []
    for o, c in zip(current_frame.open,current_frame.close):
        
        val = 0
        if o < c:
            val = 1
        elif o > c:
            val = 2
        red_or_green = {0: 'doji',
                       1: 'green',
                       2: 'red'}

        r_g.append(red_or_green[val])
    
    return r_g


def open_to_price(current_frame, price):
    open_price = list(current_frame[current_frame.time == '09:31:00'].open)[0]    
    return get_volatility([open_price], [price])
