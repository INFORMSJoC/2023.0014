import sys, os, time

from odmtsda.solve import model_c_path, model_p_path

def solve(config):

    start_time = time.time()
    print('====================================================== Stage 2')
    print('Start Time:', time.ctime(start_time))
    
    
    config._load_preprocessed_arcs()
    config._load_stage_1_alg_result()
    config._load_stage_1_postprocess_result()

    try:
        os.remove(config.s_gurobi_log_path)
    except:
        pass
    
    # import model_p_path_solution_alg
    # model_with_adopt = model_p_path_solution_alg.SolutionAlg(config)
    # model_with_adopt.run(config)

    if config.s_path_enum_alg == 'regular':
        model_with_adopt = model_c_path.OptModel(config)
    elif config.s_path_enum_alg == 'time_and_transfer_tol_specific':
        model_with_adopt = model_p_path.OptModel(config)
    else:
        raise ValueError('Impossible Path Algorithm, no matched formulation for it')

    model_with_adopt.solve()
    model_with_adopt.gen_solution_file(config)

    end_time = time.time()
    print('{} mintues are used'.format((end_time - start_time) / 60))