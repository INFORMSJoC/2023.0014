import sys, time, os

from odmtsda.path import compute_path
from odmtsda.utils import data_utils

def run(config):
    
    ### create two base graph 
    # dfs is a multi-di-graph used for depth first search
    G_dfs = compute_path.create_G_dfs(config) 


    # sp is a di-graph used for shortest path
    G_sp  = compute_path.create_G_sp(config) 

    
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
        
        ### print('-------------------------------------', i_overall_idx)
        ### first, find the best path under all conditions
        d_best_path_any = compute_path.analyze_sp(
            config,
            G_sp,
            d_trip_info,
            s_sp_term = 'obj'
        )[0]
        
        # this means we only need fixed arcs and shuttles to form this pass:
        if not d_best_path_any['has_unfixed_z']:

            # in this case, this must be equal to g_ub path
            assert(
                abs(
                    d_best_path_any['g_path']
                    -
                    d_trip_info['g_ub']
                ) < config.f_substract_epsilon
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



        ### these trips need to be considered
        ### to get set A for trip r
        i_tsf_tol = config.d_demographic[d_trip_info['trip_name']]['transfer_tolerance']
        if i_tsf_tol == -1:

            # when there is no transfer tolerance, then use sp graph, suitable for small dataset
            l_set_A_path = compute_path.analyze_sp(
                config, 
                G_sp,
                d_trip_info,
                s_sp_term = 'time'
            )

        else:

            # when there is a transfer limit, then use dfs graph, should be faster when doing large dataset
            _, l_set_A_path, _ = compute_path.analyze_dfs(
                config, 
                G_dfs,
                d_trip_info
            )
        

        ### to get set P for trip r, always use the sp graph, should be fast, this might include some paths in A, so this is called P_path_raw
        l_set_P_path_raw = compute_path.analyze_sp(
            config,
            G_sp,
            d_trip_info,
            s_sp_term = 'pft_obj'
        )


        ### merge set A and P
        l_set_AuP_path = (
            l_set_P_path_raw 
            +
            [
                x
                for x in l_set_A_path
                if x not in l_set_P_path_raw
            ]
        )        
        rank_list_with_obj(l_set_AuP_path)



        ### analyaze if the trip can be filtered out
        if len(l_set_A_path) == 0:
            
            d_path_info = {
                'only_adopt': False,
                'only_reject': True,
                'reason': 'emptyA'
            }
        
        else:

            d_path_info = {
                'only_adopt': False,
                'only_reject': False,

                'size_A': len(l_set_A_path),
                'size_P': len(l_set_AuP_path) - len(l_set_A_path),
                'size_AuP': len(l_set_AuP_path),
                'set_AuP': l_set_AuP_path
            }
                    
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