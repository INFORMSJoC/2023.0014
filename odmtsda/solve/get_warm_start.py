
from odmtsda.utils import data_utils


def run(config):

    if config.b_use_hrt_warm_start:
        return get_heuristic_warm_start(config)
    else:
        return get_basic_warm_start(config)


def get_basic_warm_start(config):

    print('Warm Start Method: All unfixed z variables are set to 0')
    d_warm_z = {}
    
    for d_arc in config.l_h2h_arcs_info:
    
        s_z_var_name = d_arc['arc_name']

        if d_arc['fixed']:
            d_warm_z[s_z_var_name] = 1
        else:
            d_warm_z[s_z_var_name] = 0
    
    return d_warm_z

def get_heuristic_warm_start(config):

    print('Warm Start Method: Heuristic Soluion')
    d_warm_z = {}

    for d_arc in config.l_h2h_arcs_info:

        s_z_var_name = d_arc['arc_name']

        if d_arc['fixed']:
            d_warm_z[s_z_var_name] = 1
        else:
            d_warm_z[s_z_var_name] = 0

    l_warm_z_hrt = data_utils.loadJson(
        config.s_hrt_warm_json_path
    )['arcs']

    for d_arc in l_warm_z_hrt:

        s_z_var_name = d_arc['arc_name']
        d_warm_z[s_z_var_name] = 1

    return d_warm_z