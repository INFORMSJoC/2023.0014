import sys, time, os

from odmtsda.path import compute_path
from odmtsda.utils import data_utils

import networkx as nx

def run(config):

    ### create two base graph 
    # dfs is a multi-di-graph used for depth first search
    G_dfs = compute_path.create_G_dfs(config) 
    G_sp  = compute_path.create_G_sp(config) 

   
    if config.b_use_brutal_dfs:
        pass
    else:

        f_time_hh_start = time.time()

        d_h2h_simple_path = compute_path.h2h_dfs(config, G_dfs)
        # d_h2h_simple_path = data_utils.loadJson(
        #     config.h2h_simple_path_json_path
        # )

        f_time_hh_end = time.time()
        print(
            'Hub to Hub Arcs are all computed, it takes {} hours.'.format(
                (f_time_hh_end - f_time_hh_start) / 3600
            )
        )
    
    ### parse additional trips
    l_addt_trips = data_utils.loadJson(
        config.preprocessed_addt_trip_json_path
    )

    l_idx_this_run = [
        i
        for i in range(len(l_addt_trips))
    ]

    ### start to iterate
    l_analyze_result = [{0 : 0}] * len(l_idx_this_run)  # pre-allocate
    for i_overall_idx in l_idx_this_run:

        d_trip_info = l_addt_trips[i_overall_idx]
        

        ### first, find the best path under all conditions
        d_best_path_any = compute_path.analyze_sp(
            config,
            G_sp,
            d_trip_info,
            s_sp_term = 'obj'
        )[0]
        
        
        # this means we only need fixed arcs and shuttles to form this path:
        if (not d_best_path_any['has_unfixed_z']) and (config.b_apply_g_ub_shuttle_arc_filter):

            # in this case, this must be equal to g_ub path
            assert(
                set(d_best_path_any['arcs']) == set(d_trip_info['arcs_in_ub'])
            )

            if d_best_path_any['adopt']:
                
                d_path_info = {
                    'only_adopt': True,
                    'only_reject': False,
                    'reason': 'anybest',
                    'only_path': d_best_path_any
                }
            
            else:
            
                d_path_info = {
                    'only_adopt': False,
                    'only_reject': True,
                    'reason': 'anybest',
                    'only_path': d_best_path_any
                }

            d_od_result_with_paths = {
                **d_trip_info,
                **d_path_info
            }

            l_analyze_result[l_idx_this_run.index(i_overall_idx)] = d_od_result_with_paths
            
            # then we don't need to worry about this trip anymore
            continue


        if config.b_use_brutal_dfs:
            l_set_Pi_path, l_set_A_path, l_set_P_path = compute_path.analyze_dfs(
                config, 
                G_dfs,
                d_trip_info,
                b_iterate_through_Pi = True
            )
        else:
            l_set_Pi_path, l_set_A_path, l_set_P_path = compute_path.analyze_dfs_with_h2h_paths(
                config, 
                G_dfs,
                d_h2h_simple_path,
                d_trip_info
            )

        ### analyaze if the trip can be filtered out
        if len(l_set_A_path) == 0 and config.b_apply_g_ub_shuttle_arc_filter:
            
            d_path_info = {
                'only_adopt': False,
                'only_reject': True,
                'reason': 'emptyA'
            }
        
        else:

            d_path_info = {
                'only_adopt': False,
                'only_reject': False,

                'size_Pi': len(l_set_Pi_path),
                'size_A': len(l_set_A_path),
                'size_P': len(l_set_P_path),
            }

            # comment it out just to test speed
            if config.b_apply_g_ub_shuttle_arc_filter:
                d_path_info['set_Pi'] = rank_list_with_obj(l_set_Pi_path)
    
                    
        d_od_result_with_paths = {
            **d_trip_info,
            **d_path_info
        }
        l_analyze_result[l_idx_this_run.index(i_overall_idx)] = d_od_result_with_paths

    ### save parsing results
    data_utils.saveJson(
        l_analyze_result,
        config.stage_1_addt_trip_result_json_path
    )

    return l_analyze_result

def rank_list_with_obj(my_list):

    my_list = sorted(
        my_list, 
        key = lambda x: x['g_path']
    )

    for i in range(len(my_list)):
        d = my_list[i]
        d['obj_rank_idx'] = i
        my_list[i] = d

    return my_list