import sys, copy

from odmtsda.utils import data_utils, other_utils

import networkx as nx


def h2h_dfs(config, G_dfs_base):

    d_h2h_simple_path = {}

    for i_orig_hub in config.l_hubs:

        for i_dest_hub in config.l_hubs:
            print(i_orig_hub, i_dest_hub)
            if i_orig_hub == i_dest_hub:
                continue
                
            simple_edge_paths = nx.all_simple_edge_paths(
                G_dfs_base, 
                str(i_orig_hub), 
                str(i_dest_hub)
            )  

            l_paths = []
            for l_edge_path in simple_edge_paths:
        
                _, f_g_path = analyze_1_OMDTS_path(
                    config,
                    None, # plce holder for d_trip_info,
                    G_dfs_base,
                    edge_path_to_node_path(l_edge_path),
                    l_edge_path,
                    b_is_multiG = True,
                    b_only_return_g_val = True
                )

                l_paths.append(
                    [
                        '_'.join(edge_path_to_node_path(l_edge_path)),
                        f_g_path
                    ]
                )


            d_h2h_simple_path[
                str(i_orig_hub) + '_' + str(i_dest_hub)
            ] = l_paths
                

    data_utils.saveJson(
        d_h2h_simple_path,
        config.h2h_simple_path_json_path
    )

    return d_h2h_simple_path

def get_possible_shuttle_idx(config, d_trip_info):

    l_possible_shuttles_idx = (
        [d_trip_info['direct_connect_idx']]
        +
        d_trip_info['from_orig_connect_idx']
        +
        d_trip_info['to_dest_connect_idx']
    )


    return [
        i_idx
        for i_idx in l_possible_shuttles_idx
    ]


def analyze_dfs_with_h2h_paths(config, G_dfs, d_h2h_simple_path, d_trip_info):

    G_trip = copy.deepcopy(G_dfs)

    i_orig_id = d_trip_info['origin_stop']
    i_dest_id = d_trip_info['destination_stop']


    l_possible_shuttles_idx = get_possible_shuttle_idx(config, d_trip_info)


    for i_arc_idx in set(l_possible_shuttles_idx): # use set to remove duplication when h2h shuttle is avaiblie 
        
        i_leg_orig_id = config.l_shuttle_arcs_info[i_arc_idx]['origin_stop']
        i_leg_dest_id = config.l_shuttle_arcs_info[i_arc_idx]['destination_stop']
        
        s_arc_orig = str(i_leg_orig_id)
        s_arc_dest = str(i_leg_dest_id)
        
        G_trip.add_edge(
            s_arc_orig, 
            s_arc_dest, 
            index = i_arc_idx, 
            mode = 'shuttle',
            obj = config.l_shuttle_arcs_info[i_arc_idx]['arc_obj_gamma'],
            time = config.l_shuttle_arcs_info[i_arc_idx]['rider_min'],
            fixed = True
        )

    l_Pi_set = []
    l_A_set  = []
    l_P_set  = []

    l_first_leg_hub_connection = [

        (
            config.l_shuttle_arcs_info[idx]['destination_stop'],
            config.l_shuttle_arcs_info[idx]['arc_obj_gamma']
        )
        for idx in d_trip_info['from_orig_connect_idx']
    ]

    if i_orig_id in config.l_hubs:
        l_first_leg_hub_connection += [
            (
                i_orig_id,
                0
            )
        ]

    l_last_leg_hub_connection = [

        (
            config.l_shuttle_arcs_info[idx]['origin_stop'],
            config.l_shuttle_arcs_info[idx]['arc_obj_gamma']
        )
        for idx in d_trip_info['to_dest_connect_idx']
    ]

    if i_dest_id in config.l_hubs:
        l_last_leg_hub_connection += [
            (
                i_dest_id,
                0
            )
        ]


    l_most_Pi = []
    for i_first_hub, f_first_leg_g in l_first_leg_hub_connection:
        for i_last_hub, f_last_leg_g in l_last_leg_hub_connection:

            if i_first_hub == i_last_hub:
                continue 

            for s_node_path, g_h2h in d_h2h_simple_path[
                str(i_first_hub) + '_' + str(i_last_hub)
            ]:

                if f_first_leg_g + g_h2h + f_last_leg_g - d_trip_info['g_ub'] > config.f_substract_epsilon:
                    continue
                
                
                l_node_path = s_node_path.split('_')

                if d_trip_info['origin_stop'] in config.l_hubs:
                    pass
                else:
                    l_node_path = [str(d_trip_info['origin_stop'])] + l_node_path
                
                if d_trip_info['destination_stop'] in config.l_hubs:
                    pass
                else:
                    l_node_path = l_node_path + [str(d_trip_info['destination_stop'])]

                l_most_Pi.append(l_node_path)



    for l_node_path in l_most_Pi + [[str(i_orig_id), str(i_dest_id)]]:
        b_consider_path, d_path_info = analyze_1_OMDTS_path(
            config,
            d_trip_info,
            G_trip,
            l_node_path,
            node_path_to_edge_path(l_node_path),
            b_is_multiG = True
        ) 

        if not b_consider_path:
            continue

        l_Pi_set.append(d_path_info)

        if (
            d_path_info['adopt'] 
        ):

            l_A_set.append(d_path_info)

        else:

            if d_path_info['b_obj_pft']:

                l_P_set.append(d_path_info)
            

    l_Pi_set = sorted(
        l_Pi_set, 
        key = lambda x: x['g_path']
    )

    l_A_set = sorted(
        l_A_set, 
        key = lambda x: x['g_path']
    )

    l_P_set = sorted(
        l_P_set, 
        key = lambda x: x['g_path']
    )

    return l_Pi_set, l_A_set, l_P_set


def analyze_dfs(config, G_dfs, d_trip_info, b_iterate_through_Pi = False):

    G_trip = copy.deepcopy(G_dfs)

    i_tsf_tol = config.d_demographic[d_trip_info['trip_name']]['transfer_tolerance']

    i_orig_id = d_trip_info['origin_stop']
    i_dest_id = d_trip_info['destination_stop']


    l_possible_shuttles_idx = get_possible_shuttle_idx(config, d_trip_info)


    for i_arc_idx in set(l_possible_shuttles_idx): # use set to remove duplication when h2h shuttle is avaiblie 
        
        i_leg_orig_id = config.l_shuttle_arcs_info[i_arc_idx]['origin_stop']
        i_leg_dest_id = config.l_shuttle_arcs_info[i_arc_idx]['destination_stop']
        
        s_arc_orig = str(i_leg_orig_id)
        s_arc_dest = str(i_leg_dest_id)
        
        G_trip.add_edge(
            s_arc_orig, 
            s_arc_dest, 
            index = i_arc_idx, 
            mode = 'shuttle',
            obj = config.l_shuttle_arcs_info[i_arc_idx]['arc_obj_gamma'],
            time = config.l_shuttle_arcs_info[i_arc_idx]['rider_min'],
            fixed = True
        )

    if (i_tsf_tol == -1) or b_iterate_through_Pi:
        simple_edge_paths = nx.all_simple_edge_paths(
            G_trip, 
            str(i_orig_id), 
            str(i_dest_id),
            cutoff = 5
        )  
    else:
        simple_edge_paths = nx.all_simple_edge_paths(
            G_trip, 
            str(i_orig_id), 
            str(i_dest_id), 

            # for example: 4 arcs = 3 transfers
            cutoff = i_tsf_tol + 1 
        )

    l_Pi_set = []
    l_A_set  = []
    l_P_set  = []
    for l_edge_path in simple_edge_paths:
        
        b_consider_path, d_path_info = analyze_1_OMDTS_path(
            config,
            d_trip_info,
            G_trip,
            edge_path_to_node_path(l_edge_path),
            l_edge_path,
            b_is_multiG = True
        ) 

        # print(b_consider_path, d_path_info)
        ### Invalid path: such as orig-hub-dest with 2 shuttles
        if not b_consider_path:
           continue

        # if break the bound
        if ((d_path_info['g_path'] - d_trip_info['g_ub']) > config.f_substract_epsilon):
            continue
        
        l_Pi_set.append(d_path_info)

        if (
            d_path_info['adopt'] 
        ):

            l_A_set.append(d_path_info)

        else:

            
            if d_path_info['b_obj_pft']:

                l_P_set.append(d_path_info)
    

    l_Pi_set = sorted(
        l_Pi_set, 
        key = lambda x: x['g_path']
    )

    l_A_set = sorted(
        l_A_set, 
        key = lambda x: x['g_path']
    )

    if (i_tsf_tol == -1) or b_iterate_through_Pi:

        l_P_set = sorted(
            l_P_set, 
            key = lambda x: x['g_path']
        )

        # when tolerance is not unlimited, the P set generated by this alg enough, but without lose of generality, we don't use this P_set if we use enhanced formulation 2
        return l_Pi_set, l_A_set, l_P_set

    else:

        # when tolerance is not unlimited, the P set generated by this alg is not enough, need to carry out k-shortest path
        return l_Pi_set, l_A_set, None


    

def analyze_sp(config, G_sp, d_trip_info, s_sp_term):

    G_trip = copy.deepcopy(G_sp)

    i_orig_id = d_trip_info['origin_stop']
    i_dest_id = d_trip_info['destination_stop']


    l_possible_shuttles_idx = get_possible_shuttle_idx(config, d_trip_info)


    for i_arc_idx in set(l_possible_shuttles_idx): # use set to remove duplication when h2h shuttle is avaiblie 
        
        i_leg_orig_id = config.l_shuttle_arcs_info[i_arc_idx]['origin_stop']
        i_leg_dest_id = config.l_shuttle_arcs_info[i_arc_idx]['destination_stop']
        s_arc_name    = config.l_shuttle_arcs_info[i_arc_idx]['arc_name']
        
        if G_trip.has_edge(
            str(i_leg_orig_id),
            str(i_leg_dest_id)
        ):  

            s_arc_orig = str(i_leg_orig_id) + '_' + s_arc_name
            s_arc_dest = str(i_leg_dest_id)

            G_trip = add_teleport(
                G_trip,
                s_arc_orig,
                str(i_leg_orig_id)
            )

        else:
            s_arc_orig = str(i_leg_orig_id)
            s_arc_dest = str(i_leg_dest_id)
        
        G_trip.add_edge(
            s_arc_orig, 
            s_arc_dest, 
            index = i_arc_idx, 
            mode = 'shuttle',
            obj = config.l_shuttle_arcs_info[i_arc_idx]['arc_obj_gamma'],
            time = config.l_shuttle_arcs_info[i_arc_idx]['rider_min'],
            fixed = True
        )

    if s_sp_term in ['obj', 'pft_obj']:
        s_weight_term = 'obj'
    else:
        s_weight_term = s_sp_term

    simple_node_paths = nx.shortest_simple_paths(
        G_trip, 
        str(i_orig_id), 
        str(i_dest_id), 
        weight = s_weight_term
    )

    l_pi_paths = []
    for i_sp_rank, l_node_path in enumerate(simple_node_paths):
        
        b_consider_path, d_path_info = analyze_1_OMDTS_path(
            config,
            d_trip_info,
            G_trip,
            l_node_path,
            node_path_to_edge_path(l_node_path)
        )

        ### In valid path: such as orig-hub-dest with 2 shuttles
        if not b_consider_path:
           continue

        ### based on different s_sp_term term, we have different stop creitiea
        # 1. when search based on pft_obj, stop searching when reach non-profitable paths
        if s_sp_term == 'pft_obj':
            if (not d_path_info['b_obj_pft']):
                break

        # 2. when search based on time, stop searching when we start to reject
        # todo: this only works based on the current time model
        elif s_sp_term == 'time':
            if (not d_path_info['adopt']):
                break
        
        # 3. when search is based on objetive, we only need the first path, and it always exist
        elif s_sp_term == 'obj':

            # the second condition is important, because the first path might be invalid shuttle paths o-hub-d
            return [d_path_info]
        else:
            raise ValueError('Wrong SP Term')
        

        l_pi_paths.append(d_path_info)
 

    

    # only keep these releveant paths
    l_pi_paths = [x for x in l_pi_paths if (x['g_path'] - d_trip_info['g_ub'] <= config.f_substract_epsilon)]
    
    l_pi_paths = sorted(
        l_pi_paths, 
        key = lambda x: x['g_path']
     )

    return l_pi_paths



def analyze_1_OMDTS_path(
    config,  
    d_trip_info,
    G_trip,
    l_node_path, 
    l_edge_path,
    b_is_multiG = False,
    b_only_return_g_val = False
):


    g_path = 0
    time_t_path = 0
    l_arcs = []
    s_path_mode = ''
    b_has_unfixed_z = False

    for s_leg_orig, s_leg_dest, i_multiedge_idx in l_edge_path:
        
        if b_is_multiG:
            d_edge = G_trip.get_edge_data(s_leg_orig, s_leg_dest)[i_multiedge_idx]
            b_has_unfixed_z = (b_has_unfixed_z or (not d_edge['fixed']))
        else:
            d_edge = G_trip.get_edge_data(s_leg_orig, s_leg_dest)
            b_has_unfixed_z = (b_has_unfixed_z or (not d_edge['fixed']))

        if d_edge['mode'] == 'shuttle':
            
            i_idx = d_edge['index']
            l_arcs.append(config.l_shuttle_arcs_info[i_idx]['arc_name'])

            f_arc_obj  = config.l_shuttle_arcs_info[i_idx]['arc_obj_gamma']
            f_arc_time = config.l_shuttle_arcs_info[i_idx]['rider_min']

            s_path_mode += 's'
        
        elif d_edge['mode'] == 'teleport':

            f_arc_obj  = 0
            f_arc_time = 0
            s_path_mode += ''

        else:
            i_idx = d_edge['index']
            l_arcs.append(config.l_h2h_arcs_info[i_idx]['arc_name'])

            f_arc_obj  = config.l_h2h_arcs_info[i_idx]['rider_obj_tau']
            f_arc_time = config.l_h2h_arcs_info[i_idx]['rider_min']

            s_path_mode += d_edge['mode'][0]


        g_path  += f_arc_obj
        time_t_path += f_arc_time

    if b_only_return_g_val:
        return None, g_path


    i_num_transfer = len(l_arcs) - 1
    b_valid_path = valid_shuttle_usage(l_arcs)
    b_is_direct = other_utils.check_if_direct_shuttle(l_arcs)

    if b_valid_path:
        
        l_no_tele_path = remove_teleport(l_node_path)

        b_adopt_status = time_transfer_based_model(
            config, 
            d_trip_info, 
            i_num_transfer,
            time_t_path
        )
        
        d_1_path = {
            'obj_rank_idx': 0,
            'arcs': l_arcs,
            'path': l_no_tele_path,
            'g_path': g_path,
            'time_t_path_min': time_t_path,
            'has_unfixed_z': b_has_unfixed_z,
            'modes': s_path_mode, 
            'b_is_direct': b_is_direct,
            'adopt': b_adopt_status,
            'b_obj_pft': g_path < (1 - config.f_convex_theta) * other_utils.get_ticket_price(config),
            'num_transfer': i_num_transfer
        }

        return b_valid_path, d_1_path
    
    else:
        return False, {0 : 0}

        


def valid_shuttle_usage(l_arcs):

    # invalid path means o-h-d with two shuttles
    if len(l_arcs) == 1:
        return True
    elif  len(l_arcs) > 1:
        
        i_shuttle_leg = len(
            [
                1
                for s_arc_name in l_arcs
                if s_arc_name[0] == 's'
            ]
        )


        if (i_shuttle_leg == len(l_arcs)) or (i_shuttle_leg > 2):
            return False
        else:
            return True

    else:
        raise ValueError('Impossible ODMTS paths for Validation') 


def remove_teleport(l_path):

    return [
        int(x)
        for x in l_path
        if '_' not in x
    ]



def edge_path_to_node_path(l):
    
    # example:
    # [('908374', '907913', 0)] -> ['908374', '907913']
    return (
        [
            x[0]
            for x in l
        ] 
        + 
        [
            l[-1][1]
        ]
    )


def node_path_to_edge_path(l):

    # example:
    # ['908374', '907913'] -> [('908374', '907913', 0)] 
    # 0 at here is a place holder, it won't matter for directed_graph
    return [
        [x, y, 0]
        for x, y in zip(l[0 : -1], l[1 :])
    ]


def add_teleport(G, s_orig, s_dest): 

    G.add_edge(
        s_orig,
        s_dest,
        index = None, 
        mode = 'teleport',
        obj = 0,
        time = 0,
        fixed = True
    )

    G.add_edge(
        s_dest,
        s_orig,
        index = None, 
        mode = 'teleport',
        obj = 0,
        time = 0,
        fixed = True
    )

    return G

def create_G_sp(config):
    
    G_sp = nx.DiGraph()

    for d_arc in config.l_h2h_arcs_info:

        if G_sp.has_edge(
            str(d_arc['origin_stop']),
            str(d_arc['destination_stop'])
        ):
            s_arc_orig = str(d_arc['origin_stop']) + '_' + d_arc['arc_name']
            s_arc_dest = str(d_arc['destination_stop'])

            G_sp = add_teleport(
                G_sp,
                s_arc_orig,
                str(d_arc['origin_stop'])
            )

        else:
            s_arc_orig = str(d_arc['origin_stop'])
            s_arc_dest = str(d_arc['destination_stop'])
        
        
        G_sp.add_edge(
            s_arc_orig,
            s_arc_dest,
            index = d_arc['id'], 
            mode = d_arc['mode'],
            obj = d_arc['rider_obj_tau'],
            time = d_arc['rider_min'],
            fixed = bool(d_arc['fixed'])
        )

    return G_sp

def create_G_dfs(config, l_ignored_arc_names = [None]):

    G_dfs = nx.MultiDiGraph()

    for d_arc in config.l_h2h_arcs_info:

        if d_arc['arc_name'] in l_ignored_arc_names:
            continue 
        
        s_arc_orig = str(d_arc['origin_stop'])
        s_arc_dest = str(d_arc['destination_stop'])
        
        G_dfs.add_edge(
            s_arc_orig,
            s_arc_dest,
            index = d_arc['id'], 
            mode = d_arc['mode'],
            obj = d_arc['rider_obj_tau'],
            time = d_arc['rider_min'],
            fixed = bool(d_arc['fixed'])
        )

    return G_dfs

def time_transfer_based_model(config, d_trip, i_num_tsf, f_rider_time):

    # Transfer Part
    if config.d_demographic[d_trip['trip_name']]['transfer_tolerance'] == -1:
        b1 = True
    else:
        b1 = (
            i_num_tsf <= (
                config.d_demographic[d_trip['trip_name']]['transfer_tolerance']
            )
        )

    # Time Part
    b2 = (
        f_rider_time <= (
            d_trip['drive_min'] 
            *
            config.d_demographic[d_trip['trip_name']]['adoption_factor']
        )
    )

    return (b1 and b2)