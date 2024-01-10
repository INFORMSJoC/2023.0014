import sys, time, os

from odmtsda.path import path_enumeration_alg_choice_specific, path_enumeration_alg_general_or_enhance, x_var_elimination
from odmtsda.utils import data_utils
def enumerate(config):

    overall_start_time = time.time()
    config._load_preprocessed_arcs()

    alg_start_time = time.time()
    print('====================================================== Stage 1 Path Enumeration Algortihm')
    print('Algorithm Start Time:', time.ctime(alg_start_time))

    if config.s_path_enum_alg == 'regular':
        l_analyze_result = path_enumeration_alg_general_or_enhance.run(config)
        s_set_name  = 'Pi'

    elif config.s_path_enum_alg == 'time_and_transfer_tol_specific':
        l_analyze_result = path_enumeration_alg_choice_specific.run(config)
        s_set_name  = 'AuP'

    else:
        raise ValueError('Impossible Algorithm')
    

    # basic stats
    s_set_size_term = 'size_' + s_set_name
    l_set_sizes = [
        x[s_set_size_term] for x in l_analyze_result
        if (not x['only_adopt']) and (not x['only_reject'])
    ]
    d_size_dist = {

        i_set_size : len(
            [
                1
                for x in l_set_sizes
                if x == i_set_size
            ]
        )
        for i_set_size in sorted(list(set(l_set_sizes)))
    }

    i_num_only_adopt = len(
        [
            1
            for x in l_analyze_result
            if x['only_adopt']
        ]
    )
    i_num_only_reject = len(
        [
            1
            for x in l_analyze_result
            if x['only_reject']
        ]
    )

    l_additioanl_TBD_set = [
        x['trip_name']
        for x in l_analyze_result
        if (not x['only_adopt']) and (not x['only_reject'])
    ]

    data_utils.saveJson(
        l_additioanl_TBD_set,
        config.additional_tbd_set_json_path
    )

    
    # post-processing
    x_eliminate_start_time = time.time()
    print('====================================================== Stage 1 Eliminate x variables')
    print('Algorithm Start Time:', time.ctime(alg_start_time))

    i_num_elimnated_x_vars = x_var_elimination.run(config)

    
    # save results
    data_utils.saveJson(
        {   
            'stage_1_full_{}'.format(
                config.computer_time_record_unit
            ): (
                (time.time() - alg_start_time) / config.i_second_divider
            ),

            'stage_1_algorithm_{}'.format(
                config.computer_time_record_unit
            ): (
                (x_eliminate_start_time - alg_start_time) / config.i_second_divider
            ),

            'stage_1_x_eliminate_{}'.format(
                config.computer_time_record_unit
            ): (
                (time.time() - x_eliminate_start_time) / config.i_second_divider
            ),
            'num_only_adopt_trip': i_num_only_adopt,
            'num_only_reject_trip': i_num_only_reject,
            'num_need_to_decided_in_MIP': len(l_analyze_result) - i_num_only_adopt - i_num_only_reject,
            'set_{}_distribution'.format(s_set_name): d_size_dist,
            '#_paths_to_deal_with': sum(l_set_sizes),
            '#_x_vars_eliminated': i_num_elimnated_x_vars
        },

        os.path.join(
            config.s_result_dir,
            'stage_1_summary.json'
        )
    )

    end_time = time.time()
    print('{} mintues are used'.format((end_time - overall_start_time) / 60))