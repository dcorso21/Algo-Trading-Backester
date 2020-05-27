import json
import os
from pathlib2 import Path


directory = Path(os.getcwd())
config_folder = directory / 'config'

form_elements = str(config_folder / 'form_elements.json')
with open(form_elements, 'r') as f:
    forms = f.read()

forms = json.loads(forms)['master']
current_config = str(directory / 'local_functions' / 'main' / 'config.json')

with open(current_config, 'r') as f:
    config_text = f.read()

config_descriptions = str(
    directory / 'local_functions' / 'main' / 'config_descriptions.json')

with open(config_descriptions, 'r') as f:
    descriptions = f.read()

descript = json.loads(descriptions)
config = json.loads(config_text)


def submission_dict(mydict, name):
    for field in mydict.keys():
        if type(mydict[field]) == dict:
            submission_dict(mydict[field], field)
        else:
            if field == 'active':
                mydict[field] = f'submission.data.{name}'
            elif field == 'priority':
                mydict[field] = f'submission.data.{name}_priority'
            else:
                mydict[field] = f'submission.data.{field}'

    return mydict


submission_form = json.loads(config_text)
meta = submission_form.pop('metaconfig')

tabs = submission_form.keys()
defaults = {}
for tab in tabs:
    defaults[tab] = f'submission.data.def_{tab}'

submission_form = submission_dict(submission_form, 'x')
submission_form['defaults'] = defaults
submission_form = json.dumps(submission_form, indent=2)
submission_form = submission_form.replace('"', '')

new_fields = []


def copy_fields(orig_dict, desc_dict):
    global new_fields
    for field in orig_dict.keys():
        if field not in desc_dict.keys():
            desc_dict[field] = orig_dict[field]
            new_fields.append(field)
        else:
            if field == desc_dict[field]:
                continue
            elif type(orig_dict[field]) == dict:
                copy_fields(orig_dict[field], desc_dict[field])

    return desc_dict


descript = copy_fields(config, descript)

if len(new_fields) != 0:
    descript = json.dumps(descript, indent=2)
    with open(config_descriptions, 'w') as f:
        f.write(descript)
    for field in new_fields:
        print(field)
    response = input(
        'the printed fields have been added to the description file. continue? [Y/n]')
    assert response.upper() == 'Y'
    print('continuing')
else:
    print('all fields accounted for')


meta = config.pop('metaconfig')


order_conditions = {
    'buy_conditions': config.pop('buy_conditions'),
    'sell_conditions': config.pop('sell_conditions')
}

param_types = {
    bool: 'checkbox',
    int: 'number',
    float: 'number',
    str: 'text',
}


tabs = []
for key in config.keys():
    tab = forms['layouts']['tab'].copy()
    tab['key'] = key
    label = key.title().replace('_', ' ')
    tab['label'] = label

    def_opt = forms['simple']['checkbox'].copy()
    def_opt['label'] = f'Default {label}'
    def_opt['defaultValue'] = False
    def_opt['key'] = f'def_{key}'

    well = forms['layouts']['well'].copy()
    well['key'] = f'well_{key}'
    well['label'] = f'Well {label}'
    well['conditional'] = {
        'show': True,
        'when': def_opt['key'],
        'eq': False,
    }

    well_components = []
    for param in config[key].keys():
        param_type = param_types[type(param)]
        component = forms['simple'][param_type].copy()
        component['defaultValue'] = config[key][param]
        component['tooltip'] = descript[key][param]
        component['key'] = param
        component['label'] = param.title().replace('_', ' ')
        well_components.append(component)

    well['components'] = well_components
    tab['components'] = [def_opt, well]
    tabs.append(tab)


def make_selections(options):
    values = []
    for i in options:
        value = {
            'label': i,
            'value': i,
        }
        values.append(value)
    data = {'values': values}
    return data


for conds in order_conditions.keys():
    tab = forms['layouts']['tab'].copy()
    tab['key'] = conds
    label = conds.title().replace('_', ' ')
    tab['label'] = label

    def_opt = forms['simple']['checkbox'].copy()
    def_opt['label'] = f'Default {label}'
    def_opt['defaultValue'] = False
    def_opt['key'] = f'def_{conds}'

    well = forms['layouts']['well'].copy()
    well['key'] = f'well_{conds}'
    well['label'] = f'Well {label}'
    well['conditional'] = {
        'show': True,
        'when': def_opt['key'],
        'eq': False,
    }
    well_components = []
    for c in order_conditions[conds].keys():
        table = forms['layouts']['table'].copy()
        table['key'] = table['label'] = f'{c}_table'
        table_components = []
        enable = forms['simple']['checkbox'].copy()
        cond_label = c.title().replace('_', ' ')
        enable['label'] = cond_label
        enable['key'] = c
        enable['defaultValue'] = order_conditions[conds][c]['active']
        enable['tooltip'] = descript[conds][c]['active']
        table_components.append(enable)

        priority = forms['simple']['number'].copy()
        priority['label'] = 'Priority'
        priority['labelPosition'] = 'right-left'
        # priority['labelMargin'] = 1
        priority['labelWidth'] = 45
        priority['key'] = f'{c}_priority'
        priority['defaultValue'] = order_conditions[conds][c]['priority']
        priority['conditional'] = {
            'show': True,
            'when': enable['key'],
            'eq': True,
        }
        table_components.append(priority)

        params = order_conditions[conds][c]
        param_desc = descript[conds][c]
        del params['active']
        del params['priority']

        if len(params) == 0:
            table_components = [{'components': [comp]}
                                for comp in table_components]
            table['rows'] = [table_components]
            well_components.append(table)
            continue

        custom = forms['simple']['checkbox'].copy()
        custom['label'] = 'Custom Parameters'
        custom['key'] = f'{c}_custom'
        custom['conditional'] = {
            'show': True,
            'when': enable['key'],
            'eq': True,
        }
        custom['defaultValue'] = False
        table_components.append(custom)

        table_components = [{'components': [comp]}
                            for comp in table_components]

        table['rows'] = [table_components]

        well_components.append(table)

        params_panel = forms['layouts']['panel'].copy()
        params_panel['title'] = f'{cond_label} Parameters'
        params_panel['key'] = f'{c}_params'
        params_panel['conditional'] = {
            'show': True,
            'when': custom['key'],
            'eq': True,
        }
        panel_components = []

        if 'advanced' in params.keys():
            advanced = params['advanced']
        for param in params.keys():
            param_type = param_types[type(param)]
            component = forms['simple'][param_type].copy()
            component['defaultValue'] = params[param]
            component['tooltip'] = param_desc[param]
            component['key'] = param
            component['label'] = param.title().replace('_', ' ')
            panel_components.append(component)

        # TODO -- ADVANCED SETTINGS

        params_panel['components'] = panel_components
        well_components.append(params_panel)

    well['components'] = well_components
    tab['components'] = [def_opt, well]
    tabs.append(tab)


wrap = forms['wrap']
wrap['components'][2]['components'] = tabs


myform = json.dumps(wrap, indent=2)
myform = f'let myform = {myform}'

form_template = str(config_folder / 'form_template.html')
with open(form_template, 'r') as f:
    template = f.read()

temp = template.replace(r'//myform', myform)
finished = temp.replace(r';//submission_form', submission_form)

with open('config_form.html', 'w') as f:
    f.write(finished)

print('form updated: config_form.html')


# print(myform)

# print('\n\n\n\n\n\n\n\n')

# print(submission_form)
