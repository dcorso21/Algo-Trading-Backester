# %%
from local_functions.main import configure
import json
import datetime

import os
from pathlib2 import Path

current_config = get_current_config()

def get_current_config():
    path = Path(os.getcwd()) 
    path = str(path / 'local_functions' / 'main' / 'config.json')
    with open(path, 'r') as f:
        current_config = f.read()

    current_config = json.loads(current_config)
    return current_config
    

def update_all(path, repo):
    # region Docstring
    '''
    # Update All
    goes through and updates the colab, default json, template file, and the ipy_creator.py file itself

    #### Returns nothing, uploads to Github

    ## Parameters:{
    ####    `path`: Path object, `gl.directory`
    ####    `repo`: github repo object for `algo_config`
    ## }
    '''
    # endregion Docstring
    path = path / 'config'
    name = path / 'config_template.json'
    with open(str(name), 'r') as f:
        template = f.read()

    name = path / 'ipy_creator.py'
    with open(str(name), 'r') as f:
        ipy_creator = f.read()

    colab_ipy = make_default_colab_ipynb(path)
    def_config = make_default_config_json()

    files = {
        'config_template.json': template,
        'ipy_creator.py': ipy_creator,
        'config_form.ipynb': colab_ipy,
        'default_config.json': def_config,
    }

    for entry in files.keys():
        contents = repo.get_contents(entry)
        repo.update_file(contents.path, "",
                         files[entry], contents.sha, branch="master")
        print(f'updated {entry}')

    print('complete')


def make_default_colab_ipynb(path):
    # region Docstring
    '''
    # Make Default Colab Ipynb
    creates an ipython notebook file based on the settings currently in the `configure.py` file      

    #### Returns nothing, saves file to this folder. 

    ## Parameters:{
    ####    `path`: path object from `gl.directory`
    ## }
    '''
    # endregion Docstring

    misc_cell = create_condition_code('misc', current_config['misc'])
    sim_settings_cell = create_condition_code('sim_settings', current_config['sim_settings'])

    bp = current_config['order_conditions']['buy_conditions']

    buy_cells = ''
    for condition in current_config['buy_conditions'].keys():
        buy_cells = buy_cells + \
            str(create_condition_code(condition, bp[condition]))+','
    
    sp = current_config['order_conditions']['sell_conditions']

    sell_cells = ''
    for condition in current_config['sell_conditions'].keys():
        sell_cells = sell_cells + \
            str(create_condition_code(condition, sp[condition]))+','

    name = path / 'config_template.json'
    with open(str(name), 'r') as f:
        text = str(f.read())
        f.close()

    import datetime

    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime(r'%m-%d-%Y at %I:%M %p')
    timestamp = f'"### Last Defaulted on {timestamp}"'

    before, after = text.split('"^^^timestamp^^^"')
    text = before + timestamp + after

    before, after = text.split('"^^^misc^^^",')
    text = before + misc_cell + ',' + after

    before, after = text.split('"^^^sim_settings^^^",')
    text = before + sim_settings_cell + ',' + after

    before, after = text.split('"^^^buy_conds^^^",')
    text = before + buy_cells + after

    before, after = text.split('"^^^sell_conds^^^",')
    default_ipy = before + sell_cells + after
    return default_ipy


def make_default_config_json(path):
    # region Docstring
    '''
    # Make Default config.json
    creates a default config.json file for comparison in google colab. 

    #### Returns the dictionary object. 

    ## Parameters:{
    ####    `path`: path object from `gl.directory`
    ## }
    '''
    # endregion Docstring

    d = current_config.copy()
    del d['metaconfig']

    timestamp = datetime.datetime.today()
    today = timestamp.strftime(r'%m-%d-%Y')
    time = timestamp.strftime(r'%I,%M_%p')

    metadata = {
        'name': 'default',
        'date': str(today),
        'time': str(time),
    }

    d['metadata'] = metadata

    d_string = json.dumps(d, indent=4, sort_keys=True)

    return d_string


def create_condition_code(dict_name, cond_dict):
    # region Docstring
    '''
    # Create Condition Code
    Creates cell contents for a code based on 
    the name of the condition/control-section and the dictionary holding the parameters

    #### Returns string object of cell with content

    ## Parameters:{
    ####    `dict_name`: name of dictionary
    ####    `cond_dict`: dictionary
    ## }
    '''
    # endregion Docstring

    lines = []
    # if condition:
    title = dict_name.title().replace('_', ' ')
    display_mode = '{display-mode: "form"}'
    title = f'#@title {title} {display_mode} \n'
    lines.append(title)
    params = ['\n', f'{dict_name}_params = '+'{\n']
    for entry in cond_dict.keys():
        param = f'    "{entry}":{entry},\n'
        value = cond_dict[entry]
        if entry == 'active':
            param = f'    "{entry}":{dict_name},\n'
            entry = dict_name
            form_type = '{type:"boolean"}'
        elif entry == 'priority':
            form_type = '["1", "2", "3", "4", "5", "6"] {type:"raw", allow-input: true}'
        else:
            if type(value) in [int, float]:
                low, high, step = calculate_constraints(value)
                form_type = '{'+f'type:"slider", min:{low}, max:{high}, step: {step}'+'}'
            elif type(value) == str:
                value = f'"{value}"'
                form_type = '{type:"raw"}'
            elif type(value) == bool:
                form_type = '{type:"boolean"}'
        line = f'{entry} = {value} #@param {form_type}\n'
        lines.append(line)
        params.append(param)
    params.append('}\n')

    lines.extend(params)
    cell = create_cell('code', lines)

    return json.dumps(cell, indent=4, sort_keys=True)


def create_cell(cell_type, content):
    # region Docstring
    '''
    # Create Cell
    Creates a Dictionary in the format of an ipython cell. 

    #### Returns cell dictionary

    ## Parameters:{
    ####    `cell_type`: str, 'code' or 'markdown',
    ####    `content`: str, dictionary conaining contents for cell. 
    ## }
    '''
    # endregion Docstring

    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": content
    }

    if cell_type == 'code':
        cell["execution_count"] = 1
        cell["outputs"] = []

    return cell


def calculate_constraints(value):
    # region Docstring
    '''
    # Calculate Constraints
    given a default value, this will return the upper and 
    lower bounds to use for a slider, as well as the iteration value. 

    #### Returns low(int), high(int) and iteration(float/int))

    ## Parameters:{
    ####    `param`:
    ## }
    '''
    # endregion Docstring
    low, high = sorted([0, value*3])

    steps = {
        '.5': .01,
        '1': .05,
        '2.5': .1,
        '5': .25,
        '10': .5,
        '20': 1,
        '100': 5,
        '250': 25,
        '500': 50,
    }

    for key in steps.keys():
        if abs(value) <= float(key):
            break

    return low, high, steps[key]


# region Unused

# def ipynb_wrap(cells, file_name):
#     # region Docstring
#     '''
#     # Ipynb Wrap
#     wraps ipynb cells into a ipynb format.
#     Basically puts the content into a template.

#     #### Returns nothing, saves file based on `file_name`

#     ## Parameters:{
#     ####    `cells`: list of cell content,
#     ####    `file_name`: path to file location, including the name
#     ## }
#     '''
#     # endregion Docstring

#     nb = {
#         "cells": cells,
#         "metadata": {
#             "language_info": {
#                 "codemirror_mode": {
#                     "name": "ipython",
#                     "version": 3
#                 },
#                 "file_extension": ".py",
#                 "mimetype": "text/x-python",
#                 "name": "python",
#                 "nbconvert_exporter": "python",
#                 "pygments_lexer": "ipython3",
#                 "version": 3
#             },
#             "orig_nbformat": 2
#         },
#         "nbformat": 4,
#         "nbformat_minor": 2
#     }
#     import json
#     with open(file_name, 'w') as f:
#         json.dump(nb, f, indent=4)
#         f.close()
#     return
# endregion Unused
