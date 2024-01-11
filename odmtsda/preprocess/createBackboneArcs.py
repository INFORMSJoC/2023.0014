import sys
from odmtsda.utils import data_utils as du

def create(config):

    ### 
    if 'backbone' not in config.l_modes:
        return []
    
    ### 
    l_backbone_arcs = create_from_json_type_backbone(config)


    return l_backbone_arcs



def create_from_json_type_backbone(config):

    l_backbone_arcs = du.loadJson(config.s_backbone_json_path)

    d_od = {
        (
            d_arc['origin_stop'], d_arc['destination_stop']
        ): {
            'frequency': d_arc['arc_avg_freq_per_hour'],
            'time_min': d_arc['avg_travel_time_min']
        }
        for d_arc in l_backbone_arcs
    }

    return [
        create_1_backbone_arc(config, d_od, t_od_key, b_set_all_to_zero = True)
        for t_od_key in d_od.keys()
    ]


def create_1_backbone_arc(config, d_od, t_od_key, b_set_all_to_zero = False):

    i_orig = t_od_key[0]
    i_dest = t_od_key[1]

    ### get all time
    f_veh_min = d_od[t_od_key]['time_min']
    f_walk_min = 0
    f_wait_min = compute_backbone_exp_wait_min(config, d_od[t_od_key]['frequency'])
    f_rider_min = (
        f_veh_min + f_walk_min + f_wait_min
    )

    if b_set_all_to_zero:

        # here frequency need to be 0, otherwise the weak connection cst will not be satisfied
        i_freq = 0
    else:
        i_freq = d_od[t_od_key]['frequency']

    return {
        # basic info
        'mode': 'backbone',
        'origin_stop': i_orig,
        'destination_stop': i_dest,

        'frequency': i_freq, 
        'fixed': True,

        # statistics
        'inv_obj_beta': 0,
        'inv_fee': 0,
        'veh_km': 0,
        'walk_km': 0,
        'veh_min': f_veh_min,
        'walk_min': f_walk_min,
        'wait_min': f_wait_min,
        'rider_min': f_rider_min,
        'rider_obj_tau': compute_backbone_rider_obj(
            config, f_rider_min
        )
    }


def compute_backbone_exp_wait_min(config, i_freq_per_hour):
    
    if config.i_backbone_wait_method == 0:
        return 0

    elif config.i_backbone_wait_method == 1:
        # unit in min
        return (60 / i_freq_per_hour / 2)

    else:
        raise ValueError()


def compute_backbone_rider_obj(
    config, f_rider_min
):
    return (
        f_rider_min * config.f_time_convex_fac
        * 
        config.f_convex_theta
    )