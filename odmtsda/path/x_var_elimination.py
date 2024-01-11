import sys, time, os

from odmtsda.path import compute_path
from odmtsda.utils import data_utils

import networkx as nx


def run(config):
    
    l_additioanl_TBD_set = data_utils.loadJson(
        config.additional_tbd_set_json_path
    )

    # create initaila file
    d_arc_trip_relation = {
        d_arc['arc_name']: None
        for d_arc in config.l_h2h_arcs_info
    }

    i_num_elimnated_x_vars = 0
    for d_arc in config.l_h2h_arcs_info:

        # print('Workgin on arc {}'.format(d_arc['arc_name']))
        
        G_check_graph = compute_path.create_G_dfs(
            config,
            l_ignored_arc_names = [
                d_arc['arc_name']
            ]
        )

        d_arc_trip_relation[
            d_arc['arc_name']
        ] = b_get_bus_train_arc_filter_result(
            config,
            G_check_graph,
            l_additioanl_TBD_set,
            d_arc
        )

        i_num_elimnated_x_vars += sum(d_arc_trip_relation[d_arc['arc_name']].values())

    # data
    data_utils.saveJson(
        d_arc_trip_relation,
        config.stage_1_postprocess_result_json_path
    )


    return i_num_elimnated_x_vars
    



def b_get_bus_train_arc_filter_result(
    config, G_check_graph, l_additioanl_TBD_set, d_arc
):


    l_consider_trips = []
    # l_consider_trips += config.l_core_stage_1_res
    
    d_trip_decision = {}
    for d_trip in data_utils.loadJson(
        config.preprocessed_addt_trip_json_path
    ):
        if d_trip['trip_name'] not in l_additioanl_TBD_set:
            continue
        
        if d_arc['arc_name'] in d_trip['h2h_arcs_in_ub']:
            d_trip_decision[d_trip['trip_name']] = False
        else:
            l_consider_trips.append(d_trip)
            d_trip_decision[d_trip['trip_name']] = None # pre-allocate


    set_all_possible_shuttles_idx = set()
    for d_trip in l_consider_trips:
        set_od_possible_shuttles_idx = set(
            [d_trip['direct_connect_idx']]
            +
            d_trip['from_orig_connect_idx']
            +
            d_trip['to_dest_connect_idx']
        )

        set_all_possible_shuttles_idx = set_all_possible_shuttles_idx.union(
            set_od_possible_shuttles_idx
        )



    for i_arc_idx in set_all_possible_shuttles_idx: # use set to remove duplication when h2h shuttle is avaiblie 
        
        i_leg_orig_id = config.l_shuttle_arcs_info[i_arc_idx]['origin_stop']
        i_leg_dest_id = config.l_shuttle_arcs_info[i_arc_idx]['destination_stop']
        
        s_arc_orig = str(i_leg_orig_id)
        s_arc_dest = str(i_leg_dest_id)
        

        G_check_graph.add_edge(
            s_arc_orig, 
            s_arc_dest, 
            index = i_arc_idx, 
            mode = 'shuttle',
            obj = config.l_shuttle_arcs_info[i_arc_idx]['arc_obj_gamma'],
            time = config.l_shuttle_arcs_info[i_arc_idx]['rider_min'],
            fixed = True
        )


    s_arc_orig_id = str(d_arc['origin_stop'])
    s_arc_dest_id = str(d_arc['destination_stop'])
    G_check_graph.add_node(s_arc_orig_id)
    G_check_graph.add_node(s_arc_dest_id)


    d_obj_to_arc_orig = nx.shortest_path_length(
        G_check_graph,
        target = s_arc_orig_id, 
        weight = 'obj', 
        method = 'dijkstra'
    )

    d_obj_from_arc_dest = nx.shortest_path_length(
        G_check_graph,
        source = s_arc_dest_id, 
        weight = 'obj', 
        method = 'dijkstra'
    )

    for d_trip in l_consider_trips:

        s_trip_orig_id = str(d_trip['origin_stop'])
        s_trip_dest_id = str(d_trip['destination_stop'])

        if s_trip_orig_id not in d_obj_to_arc_orig.keys():
            pass
        else:

            if d_obj_to_arc_orig[s_trip_orig_id] + d_arc['rider_obj_tau'] - d_trip['g_ub'] > config.f_substract_epsilon:
                d_trip_decision[d_trip['trip_name']] = True
                continue

        if s_trip_dest_id not in d_obj_from_arc_dest.keys():
            pass
        else:
            if d_arc['rider_obj_tau'] + d_obj_from_arc_dest[s_trip_dest_id] - d_trip['g_ub'] > config.f_substract_epsilon:
                d_trip_decision[d_trip['trip_name']] = True
                continue 

        d_trip_decision[d_trip['trip_name']] = False

    return d_trip_decision