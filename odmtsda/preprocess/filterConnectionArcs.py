import sys, copy

import networkx as nx, numpy as np
from odmtsda.utils import data_utils as du
from odmtsda.preprocess import createConnectionArcs
    
def create_graph_fixed_arcs(config):

    l_h2h_arcs_info = du.loadJson(config.h2h_arcs_json_path)

    graph_fixed = nx.MultiDiGraph()
    
    if not config.b_use_backbone_ub_to_filter:
        pass
    else:
        for d_arc in l_h2h_arcs_info:

            if not d_arc['fixed']:
                continue
            
            i_arc_orig = d_arc['origin_stop']
            i_arc_dest = d_arc['destination_stop']
            
            
            graph_fixed.add_edge(
                i_arc_orig,
                i_arc_dest,
                obj = d_arc['rider_obj_tau'],
                arc_name = 'z{}'.format(d_arc['id'])
            )

    return graph_fixed


def compute_trip_g_ub_then_filter(config, graph_fixed, i_orig, i_dest):

    ### get related connect arcs for this trip
    i_direct_idx = config.d_connect_arc_name_map[
        '{}_{}'.format(
            i_orig,
            i_dest
        )
    ]
    l_orig_connect_ods, l_dest_connect_ods = createConnectionArcs.get_hub_connect_legs(
        config, i_orig, i_dest
    )

    ### create the trip graph
    G_trip = copy.deepcopy(graph_fixed)


    # ### add the direct connect arc 
    d_direct_arc = config.l_shuttle_arcs_info[i_direct_idx]
    f_direct_obj = d_direct_arc['arc_obj_gamma']
    G_trip.add_edge(
        i_orig,
        i_dest,
        obj = f_direct_obj,
        arc_name = d_direct_arc['arc_name']
    )


    ### process orig-hub connects
    l_orig_fix_graph_connect_idx = []
    for (i_arc_orig, i_arc_dest) in l_orig_connect_ods:
        
        # get arc info
        i_arc_idx = config.d_connect_arc_name_map[
            '{}_{}'.format(
                i_arc_orig,
                i_arc_dest
            )
        ]
        d_arc = config.l_shuttle_arcs_info[i_arc_idx]
        
        # add to fix graph
        if d_arc['arc_obj_gamma'] <= f_direct_obj: 
            G_trip.add_edge(
                i_arc_orig,
                i_arc_dest, 
                obj = d_arc['arc_obj_gamma'],
                arc_name = d_arc['arc_name']
            )
            l_orig_fix_graph_connect_idx.append(i_arc_idx)


    ### process hub-dest connects
    l_dest_fix_graph_connect_idx = []
    for (i_arc_orig, i_arc_dest) in l_dest_connect_ods:

        # get arc info
        i_arc_idx = config.d_connect_arc_name_map[
            '{}_{}'.format(
                i_arc_orig,
                i_arc_dest
            )
        ]
        d_arc = config.l_shuttle_arcs_info[i_arc_idx]

        # add to fix graph
        if d_arc['arc_obj_gamma'] <= f_direct_obj: 
            G_trip.add_edge(
                i_arc_orig,
                i_arc_dest, 
                obj = d_arc['arc_obj_gamma'],
                arc_name = d_arc['arc_name']
            )
            l_dest_fix_graph_connect_idx.append(i_arc_idx)


    ### compute the trip's objective upper-bound
    l_shortest_path = nx.shortest_path(
        G_trip, 
        source = i_orig, 
        target = i_dest, 
        weight = 'obj', 
        method = 'dijkstra'
    )


    ### compute the fixe-arc path that create that upperbound, in case we have overlapping h2h arcs
    f_trip_g_ub = 0
    l_arcs_in_ub = []
    for [i_arc_orig, i_arc_dest] in zip(
        l_shortest_path[0 : -1], 
        l_shortest_path[1 :]
    ):
        d_edges = G_trip.get_edge_data(i_arc_orig, i_arc_dest)
        
        i_multi_edge_idx = np.argmin(
            [
                d_edges[x]['obj']
                for x in d_edges.keys()
            ]
        )

        d_best_edge = d_edges[i_multi_edge_idx]

        l_arcs_in_ub.append(d_best_edge['arc_name'])
        f_trip_g_ub += d_best_edge['obj']


    ### use networkx to compute the ub again, just to double check
    f_nx_ub = nx.shortest_path_length(
        G_trip, 
        source = i_orig, 
        target = i_dest, 
        weight = 'obj', 
        method = 'dijkstra'
    )
    assert(
        (f_trip_g_ub - f_nx_ub) <= config.f_substract_epsilon
    )


    # further filter out some connect arcs using the newly-computed upper-bound
    l_orig_connect_idx = [
        idx
        for idx in l_orig_fix_graph_connect_idx
        if config.l_shuttle_arcs_info[idx]['arc_obj_gamma'] <= f_trip_g_ub
    ]

    l_dest_connect_idx = [
        idx
        for idx in l_dest_fix_graph_connect_idx
        if config.l_shuttle_arcs_info[idx]['arc_obj_gamma'] <= f_trip_g_ub
    ]

    return l_arcs_in_ub, f_trip_g_ub, l_orig_connect_idx, l_dest_connect_idx