# %%
from local_functions.main import controls
import json

sp = controls.sell_cond_params
bp = controls.buy_cond_params
misc = controls.misc


def create_cell(cell_type, content):

    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": content
    }

    if cell_type == 'code':
        cell["execution_count"] = 1
        cell["outputs"] = []

    return cell


def ipynb_wrap(cells, file_name):
    nb = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": 3
            },
            "orig_nbformat": 2
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    import json
    with open(file_name, 'w') as f:
        json.dump(nb, f, indent=4)
        f.close()
    return


def calculate_constraints(value):
    low, high = sorted([0, value*3])

    steps = {
        '10': .5,
        '20': 1,
        '100': 5,
        '250': 25,
        '500': 50,
    }

    for step in steps.keys():
        if abs(value) <= int(step):
            break

    return low, high, steps[step]


def create_condition_code(dict_name, cond_dict):

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


def make_default_colab_ipynb(path):

    misc_cell = create_condition_code('misc', misc)

    buy_cells = ''
    for condition in bp.keys():
        buy_cells = buy_cells + \
            str(create_condition_code(condition, bp[condition]))+','

    sell_cells = ''
    for condition in sp.keys():
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

    before, after = text.split('"^^^buy_conds^^^",')
    text = before + buy_cells + after

    before, after = text.split('"^^^sell_conds^^^",')
    default_ipy = before + sell_cells + after
    return default_ipy


def make_default_config_json(path):
    d = {
        'misc': misc,
        'order_conditions': {'buy_conditions': bp, 'sell_conditions': sp}
    }

    d = json.dumps(d, indent=4, sort_keys=True)
    name = path / 'default_config.json'
    with open(str(name), 'w') as f:
        f.write(d)
        f.close()

    return d


def update_all(path, repo):
    path = path / 'config'
    name = path / 'config_template.json'
    with open(str(name), 'r') as f:
        template = f.read()

    name = path / 'ipy_creator.py'
    with open(str(name), 'r') as f:
        ipy_creator = f.read()

    colab_ipy = make_default_colab_ipynb(path)
    def_config = make_default_config_json(path)

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
