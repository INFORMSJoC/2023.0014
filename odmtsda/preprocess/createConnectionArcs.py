import sys
from odmtsda.utils import data_utils as du

import pandas as pd

def create(config):


    # process core trips
    df_core_trips = pd.read_csv(
        config.s_core_ODs_csv_path
    )


    # process latent trips
    df_latent_trips = pd.read_csv(
        config.s_latent_ODs_csv_path
    )
    df_all_trips = pd.concat([df_core_trips, df_latent_trips])


    d_connect_arc_name_map, l_connect_arcs = get_connections(config, df_all_trips)

    du.saveJson(
        d_connect_arc_name_map,
        config.shuttle_arcs_refer_json_path
    )
    
    du.saveJson(
        l_connect_arcs,
        config.shuttle_arcs_json_path
    )



def get_connections(config, df_all_trips):
    
    # intialize
    set_connect_ods = set()
    for _, df_row in df_all_trips.iterrows():

        
        ### Origin to Hubs, Hubs to Destinations
        l_orig_connect_ods, l_dest_connect_ods = get_hub_connect_legs(
            config, 
            int(df_row['start_stop']),
            int(df_row['end_stop'])
        )

        set_connect_ods = set_connect_ods.union(
            set(l_orig_connect_ods)
        )

        set_connect_ods = set_connect_ods.union(
            set(l_dest_connect_ods)
        )


        ### Direct Trips
        set_connect_ods.add(
            (
                int(df_row['start_stop']), 
                int(df_row['end_stop'])
            )
        )

    ### compute all used
    l_connect_ods = sorted(list(set_connect_ods))

    l_connect_arcs = [
        create_1_connect_arc(
            config, 
            i_idx = i,
            i_orig = l_connect_ods[i][0], 
            i_dest = l_connect_ods[i][1]
        )
        for i in range(len(l_connect_ods))
    ]

    d_connect_arc_name_map = {
        '{}_{}'.format(l_connect_ods[i][0], l_connect_ods[i][1]) : i
        for i in range(len(l_connect_ods))
    }


    return d_connect_arc_name_map, l_connect_arcs



def get_hub_connect_legs(config, i_orig, i_dest):

    ### possible connect arcs, trip origin to hubs
    if (
        (not config.b_shuttle_allow_h2h) 
        and 
        (i_orig in config.l_hubs)
    ):  
        l_orig_connect_ods = []
    else:
        l_orig_connect_ods = [
            (i_orig, i_hub_id)
            for i_hub_id in config.l_hubs
        ]
    
    ### possible connect arcs, hubs to trip destination to solve the problem
    if (
        (not config.b_shuttle_allow_h2h)
        and 
        (i_dest in config.l_hubs)
    ):  
        l_dest_connect_ods = []
    else:
        l_dest_connect_ods = [
            (i_hub_id, i_dest)
            for i_hub_id in config.l_hubs
        ]
    
    return l_orig_connect_ods, l_dest_connect_ods


def create_1_connect_arc(
    config,
    i_idx,
    i_orig,
    i_dest
):


    ### Distance
    f_veh_km = config.d_dist[(i_orig, i_dest)]


    ### Time
    f_veh_min = config.d_time[(i_orig, i_dest)]
    f_wait_min = config.f_shuttle_wait_min
    f_rider_min = (
        f_veh_min + f_wait_min
    )


        
    ### get cost and obj
    f_opt_cost, f_obj = compute_connect_arc_cost(
        config, 
        f_veh_km,
        f_veh_min,
        f_rider_min
    )

    return {
        'id': i_idx,
        'arc_name': '{}{}'.format('s', i_idx),
        'mode': config.s_connect_mode,
        'origin_stop': i_orig,
        'destination_stop': i_dest,
        'veh_km': f_veh_km,
        'walk_km': 0,
        'veh_min': f_veh_min,
        'walk_min': 0,
        'wait_min': f_wait_min,
        'rider_min': f_rider_min,
        'operating_cost': f_opt_cost,
        'arc_obj_gamma': f_obj
    }


def compute_connect_arc_cost(config, f_veh_km, f_veh_min, f_rider_min):

    if config.s_shuttle_cost_version == 'distance':
        f_opt_cost = (
            f_veh_km
            *
            config.f_shuttle_cost_per_km
        )
    elif config.s_shuttle_cost_version == 'time':
        f_opt_cost = (
            f_veh_min / 60
            *
            config.f_shuttle_cost_per_hour
        )
    else:
        raise ValueError

    return(
        # operating costs $
        f_opt_cost,

        # operating weighted cost
        (
            f_opt_cost * (1 - config.f_convex_theta)
            +
            f_rider_min * config.f_time_convex_fac
            *
            config.f_convex_theta
        )
    )
