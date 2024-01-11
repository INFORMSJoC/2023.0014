import sys
from odmtsda.utils import data_utils as du

def create(config, l_all_backbone_arcs):

    ### Intialize
    if 'backbone' in config.l_modes:
        l_backbone_hubs = du.loadJson(config.s_backbone_hubs_json_path)
    else:
        l_backbone_hubs = []
    
    l_bus_only_hubs = [
        i_hub
        for i_hub in config.l_hubs
        if i_hub not in l_backbone_hubs
    ]

    l_bus_arcs = (
        backbone_hub_and_backbone_hub(config, l_backbone_hubs)
        +
        bus_only_hub_and_bus_only_hub(config, l_bus_only_hubs)
        +
        bus_only_hub_and_backbone_hub(config, l_bus_only_hubs, l_backbone_hubs, l_all_backbone_arcs)
    )

    return remove_duplicate(l_bus_arcs)


def backbone_hub_and_backbone_hub(config, l_backbone_hubs):

    return []

def bus_only_hub_and_bus_only_hub(config, l_bus_only_hubs):

    l_arcs = []
    for i_orig in l_bus_only_hubs:


        ### Determined allowed bus-only-hub -> bus-only-hub
        if config.i_bus_bus_connect_lim == -1:
            l_allowed_dest_hubs = [
                i_hub
                for i_hub in l_bus_only_hubs
                if i_orig != i_hub
            ]
        else:
            l_dest_hubs_sorted = sorted(
                [
                    (
                        i_hub, 
                        config.d_time[(i_orig, i_hub)]
                    )
                    for i_hub in l_bus_only_hubs
                    if i_orig != i_hub
                ],
                key = lambda x: x[1]
            )
            l_allowed_dest_hubs = [
                i_hub
                for (i_hub, _) in l_dest_hubs_sorted[0 : config.i_bus_bus_connect_lim]
            ]

        
        for i_dest in l_allowed_dest_hubs:
            
            ### Start to creat 
            for i_freq_per_hour in config.t_bus_frequencies:

                d_bus_arc = new_1_bus_arc(
                    config,
                    i_orig = i_orig,
                    i_dest = i_dest,
                    i_freq_per_hour = i_freq_per_hour
                )
                l_arcs.append(
                    d_bus_arc
                )

                ### Reverse it
                d_bus_arc = new_1_bus_arc(
                    config,
                    i_orig = i_dest,
                    i_dest = i_orig,
                    i_freq_per_hour = i_freq_per_hour
                )
                l_arcs.append(
                    d_bus_arc
                )


    return l_arcs

def bus_only_hub_and_backbone_hub(config, l_bus_only_hubs, l_backbone_hubs, l_all_backbone_arcs):

    ###
    l_allowed_ods = []
    for i_orig in l_bus_only_hubs:

        ### Determined allowed bus-only-hub -> backbone-hub
        if config.i_bus_rail_connect_lim == -1:
            l_allowed_dest_hubs = [
                i_hub
                for i_hub in l_backbone_hubs
                if i_hub != i_orig
            ]
        else:
            l_dest_hubs_sorted = sorted(
                [
                    (
                        i_hub, 
                        config.d_time[(i_orig, i_hub)]
                    )
                    for i_hub in l_backbone_hubs
                    if i_hub != i_orig
                ],
                key = lambda x: x[1]
            )
            l_allowed_dest_hubs = [
                i_hub
                for (i_hub, _) in l_dest_hubs_sorted[0 : config.i_bus_rail_connect_lim]
            ]


        for i_dest in l_allowed_dest_hubs:
            
            # Start to add ODs.
            l_allowed_ods.append([i_orig, i_dest])
            l_allowed_ods.append([i_dest, i_orig])


            # Exceptions: Make these backbone hubs connected, so it is easier to create cycles
            for i_dest_2 in l_allowed_dest_hubs:
                if i_dest == i_dest_2:
                    continue
                else:
                    l_allowed_ods.append([i_dest, i_dest_2])



    ### Know what O-D pairs are already covered by backbone
    l_backbone_ods = [
        [d_arc['origin_stop'], d_arc['destination_stop']]
        for d_arc in l_all_backbone_arcs
    ]

    l_arcs = []
    for [i_orig, i_dest] in l_allowed_ods:
        if (not config.b_allow_bus_backbone_overlap) and ([i_orig, i_dest] in l_backbone_ods):
            pass
        else:
            
            for i_freq_per_hour in config.t_bus_frequencies:

                ### No need to reverse here, all reversed one are already in l_allowed_ods       
                d_bus_arc = new_1_bus_arc(
                    config,
                    i_orig = i_orig,
                    i_dest = i_dest,
                    i_freq_per_hour = i_freq_per_hour
                )
                l_arcs.append(
                    d_bus_arc
                )

    return l_arcs


def new_1_bus_arc(
    config, 
    i_orig, 
    i_dest, 
    i_freq_per_hour
):

    ### get distance
    f_veh_km = config.d_dist[(i_orig, i_dest)]

    ### get all time
    f_veh_min = config.d_time[(i_orig, i_dest)]
    f_walk_min = 0
    f_wait_min = compute_newbus_exp_wait_min(config, i_freq_per_hour)
    f_rider_min = (
        f_veh_min + f_walk_min + f_wait_min
    )

    ### get all cost
    f_inv_fee, f_inv_obj_beta = compute_newbus_investment_cost(
        config, 
        i_orig, 
        i_dest,
        i_freq_per_hour
    )

    return {
        # basic info
        'mode': 'bus',
        'origin_stop': i_orig,
        'destination_stop': i_dest,
        'frequency': i_freq_per_hour,
        'fixed': False,

        # statistics
        'inv_obj_beta': f_inv_obj_beta,
        'inv_fee': f_inv_fee,
        'veh_km': f_veh_km,
        'walk_km': 0,
        'veh_min': f_veh_min,
        'walk_min': f_walk_min,
        'wait_min': f_wait_min,
        'rider_min': f_rider_min,
        'rider_obj_tau': compute_newbus_rider_obj(
            config, f_rider_min
        )
    }


def compute_newbus_exp_wait_min(config, i_freq_per_hour):
    
    if config.i_bus_wait_method == 0:
        return 0

    elif config.i_bus_wait_method == 1:
        # unit in min
        return (60 / i_freq_per_hour / 2)

    else:
        raise ValueError()


def compute_newbus_rider_obj(config, f_rider_min):

    return (
        f_rider_min * config.f_time_convex_fac
        * 
        config.f_convex_theta
    )

def compute_newbus_investment_cost(config, i_orig, i_dest, i_freq_per_hour):

    f_time_horizon_in_hours = (
        config.f_horizon_end_hour - config.f_horizon_start_hour
    )
    
    if config.s_bus_cost_version == 'distance':
    
        f_inv_fee = (
            i_freq_per_hour
            *
            f_time_horizon_in_hours
            *
            config.d_dist[(i_orig, i_dest)]
            *
            config.f_bus_cost_per_km
        )

    elif config.s_bus_cost_version == 'time':
        
        f_inv_fee = (
            i_freq_per_hour
            *
            f_time_horizon_in_hours
            *
            config.d_time[(i_orig, i_dest)] / 60
            *
            config.f_bus_cost_per_hour
        )

    else:
        raise ValueError


    return (
        # in US dollar
        f_inv_fee,

        # weighted cost
        f_inv_fee * (1 - config.f_convex_theta)
    )


def remove_duplicate(l_arcs):

    l_arcs_clean = []
    set_arcs_appear = set()

    for d_arc in l_arcs:
        t_arc_info = (
            d_arc['origin_stop'],
            d_arc['destination_stop'],
            d_arc['frequency']
        )

        if t_arc_info in set_arcs_appear:
            pass
        else:
            set_arcs_appear.add(t_arc_info)
            l_arcs_clean.append(d_arc)

    return l_arcs_clean