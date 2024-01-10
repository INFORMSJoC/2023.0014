import sys
from odmtsda.utils import data_utils as du
from odmtsda.preprocess import filterConnectionArcs

import pandas as pd


def create(config):


    ### Load arcs
    config._load_preprocessed_arcs()

    ### Filter Arcs
    graph_fixed = filterConnectionArcs.create_graph_fixed_arcs(config)

    ### Process Core Trips
    df_core_trips = pd.read_csv(
        config.s_core_ODs_csv_path
    )
    l_core_trips = create_trips(config, graph_fixed, df_core_trips, 'c')
    du.saveJson(
        l_core_trips,
        config.preprocessed_core_trip_json_path
    )  


    ### Process Latent Trips
    df_latent_trips = pd.read_csv(
        config.s_latent_ODs_csv_path
    )
    l_latent_trips = create_trips(config, graph_fixed, df_latent_trips, 'l')
    
    du.saveJson(
        l_latent_trips,
        config.preprocessed_addt_trip_json_path
    )  


def create_trips(config, graph_fixed, df_trips, s_trip_type):
    
    return [
        create_1_trip(
            config,
            graph_fixed,
            df_row,
            i_trip_idx,
            s_trip_name = s_trip_type + str(i_trip_idx)
        )
        for i_trip_idx, df_row in df_trips.iterrows()
    ]

def create_1_trip(
    config, 
    graph_fixed, 
    df_row,
    i_trip_idx,
    s_trip_name
):  

    ### Get Data
    i_trip_orig  = int(df_row['start_stop'])
    i_trip_dest  = int(df_row['end_stop'])

    ### get trip obj upper bound, then use it filter arcs (not direct arcs though)
    (
        l_h2h_arcs_in_ub, 
        f_trip_g_ub, 
        l_orig_connect_idx, 
        l_dest_connect_idx
    ) = filterConnectionArcs.compute_trip_g_ub_then_filter(
        config, 
        graph_fixed, 
        i_trip_orig, 
        i_trip_dest
    )


    ### get the direct path and its obj
    i_direct_idx = config.d_connect_arc_name_map[
        '{}_{}'.format(i_trip_orig, i_trip_dest)
    ]
    f_direct_obj = config.l_shuttle_arcs_info[i_direct_idx]['arc_obj_gamma']

    return {

        # key information
        'idx_in_set': i_trip_idx,
        'trip_name': s_trip_name,
        'origin_stop': i_trip_orig,
        'destination_stop': i_trip_dest,
        'num_riders': int(df_row['counts']) * config.i_pax_multip,
        

        # related to latent demand, latent demand = l
        'is_core_trip': bool(s_trip_name[0] == 'c'),
                
        
        # direct trips
        'drive_km': config.d_dist[(i_trip_orig, i_trip_dest)],
        'drive_min': config.d_time[(i_trip_orig, i_trip_dest)],
        'direct_obj': f_direct_obj,


        # upper-bound
        'g_ub': f_trip_g_ub,
        'h2h_arcs_in_ub': l_h2h_arcs_in_ub, 


        # arc indices
        'direct_connect_idx': i_direct_idx,
        'from_orig_connect_idx': sorted(l_orig_connect_idx),
        'to_dest_connect_idx': sorted(l_dest_connect_idx)
    }