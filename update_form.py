import json
import os
from pathlib import Path


directory = Path(os.getcwd())
config_folder = directory / 'config'


# FORM ELEMENTS
form_elements = str(config_folder / 'form_elements.json')
with open(form_elements, 'r') as f:
    forms = f.read()
forms = json.loads(forms)['master']


# CURRENT CONFIG
current_config = str(directory / 'local_functions' / 'main' / 'config.json')
with open(current_config, 'r') as f:
    config_text = f.read()
config = json.loads(config_text)


# CURRENT CONFIG DESCRIPTIONS
config_descriptions = str(
    directory / 'local_functions' / 'main' / 'config_descriptions.json')
with open(config_descriptions, 'r') as f:
    descriptions = f.read()
descript = json.loads(descriptions)


def submission_dict(mydict, name):
    # region Docstring
    '''
    # Submission Dictionary
    Takes the current configuration and creates a template for the submitted data.

    #### Returns dictionary of values for new configuration

    ## Parameters:{
    ####    `mydict`: dictionary to create submission values for
    ####    `name`: dict name. because of the `active` field being named after the conditions in the form.
    ## }
    '''
    # endregion Docstring
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


# CREATE SUBMISSION FORM
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


def update_descriptions(c, d):
    def copy_fields(orig_dict, desc_dict, new_fields=[]):
        # region Docstring
        '''
        # Copy Fields
        Copies each field not in the description dictionary.

        #### Returns description dict

        ## Parameters:{
        ####    `orig_dict`: dict to be copied from.
        ####    `desc_dict`: dict to be copied to.
        ####    `new_fields`: dict to be copied to.
        ## }
        '''
        # endregion Docstring
        for field in orig_dict.keys():
            if field not in desc_dict.keys():
                desc_dict[field] = orig_dict[field]
                new_fields.append(field)
            else:
                if field == desc_dict[field]:
                    continue
                elif type(orig_dict[field]) == dict:
                    copy_fields(orig_dict[field], desc_dict[field], new_fields)

        return desc_dict, new_fields

    d, new_fields = copy_fields(c, d)

    if len(new_fields) != 0:
        d_updated = json.dumps(d, indent=2)
        with open(config_descriptions, 'w') as f:
            f.write(d_updated)
        for field in new_fields:
            print(field)
        response = input(
            '\nthe printed fields have been added to the description file. continue?\n[Y/n]:')
        assert response.upper() == 'Y'
        print('continuing')
    else:
        print('all fields accounted for')

    return d


descript = update_descriptions(config, descript)

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

# CREATING NON-ORDER TABS
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
        param_type = param_types[type(config[key][param])]
        component = forms['simple'][param_type].copy()
        component['defaultValue'] = config[key][param]
        component['tooltip'] = descript[key][param]
        component['key'] = param
        component['label'] = param.title().replace('_', ' ')
        well_components.append(component)

    well['components'] = well_components
    tab['components'] = [def_opt, well]
    tabs.append(tab)


# CREATING ORDER TABS
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

from local_functions.main import global_vars as gl
configs = gl.get_downloaded_configs()




# region UNUSED


# def make_selections(options):
#     # DEPRECATED
#     values = []
#     for i in options:
#         value = {
#             'label': i,
#             'value': i,
#         }
#         values.append(value)
#     data = {'values': values}
#     return data

# endregion UNUSED
