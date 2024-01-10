import sys, os, git
import pandas as pd
from odmtsda.utils import data_utils as du


class Configuration():

    def __init__(self):

        self.s_git_dir = git.Repo(".", search_parent_directories=True).working_tree_dir
        self.d_args = du.generate_argParser()
        self._load_parameters()
        self._create_folder_names()
        self._form_file_paths()


        if self.computer_time_record_unit == 'hours':
            self.i_second_divider = 3600
        elif self.computer_time_record_unit == 'minutes':
            self.i_second_divider = 60
        else:
            raise ValueError('Wrong Computing Time Unit')
        
        
         


    def _load_parameters(self):
        
        self.d_yaml_pars = du.loadYaml(
            self.d_args['s_par_yaml_path']
        )
        for key in self.d_yaml_pars:
            self.d_args[key] = self.d_yaml_pars[key]

        # change all to attribute
        for key in self.d_args:
            setattr(self, key, self.d_args[key])


    def _create_folder_names(self):
        
        self.d_yaml_dir_path = du.loadYaml(
            self.d_args['s_dir_and_path_input_yaml_path']
        )

        # raw data dir
        self.s_raw_data_dir = os.path.join(
            self.s_git_dir,
            self.d_yaml_dir_path['s_raw_data_dir']
        )
        assert(os.path.isdir(self.s_raw_data_dir))


        # preprocessed dir
        self.s_prepare_dir = os.path.join(
            self.s_git_dir,
            self.d_yaml_dir_path['s_overall_prepare_result_dir']
        )
        du.checkDir(self.s_prepare_dir)


        # result dir
        self.s_result_dir = os.path.join(
            self.s_git_dir,
            self.d_yaml_dir_path['s_overall_result_dir']
        )
        du.checkDir(self.s_result_dir)
        print('Result directory is {}'.format(self.s_result_dir))



    def _form_file_paths(self):
        
        # some raw data and prepare folder
        self.s_demographic_json_path = os.path.join(
            self.s_raw_data_dir,
            'demographic.json'
        )

        self.s_stop_csv_path = os.path.join(
            self.s_raw_data_dir,
            'stops.csv'
        )

        self.s_dist_km_pickle_path = os.path.join(
            self.s_raw_data_dir,
            'dist_km.pickle'
        )

        self.s_time_min_pickle_path = os.path.join(
            self.s_raw_data_dir,
            'time_min.pickle'
        )

        self.s_hub_csv_path = os.path.join(
            self.s_raw_data_dir,
            'hubs.csv'
        )

        self.s_core_ODs_csv_path = os.path.join(
            self.s_raw_data_dir,
            'core-trips.csv'
        )

        self.s_latent_ODs_csv_path = os.path.join(
            self.s_raw_data_dir,
            'latent-trips.csv'
        )

        self.h2h_arcs_json_path = os.path.join(
            self.s_prepare_dir,
            'network_h2h_arcs.json'
        )

        self.shuttle_arcs_refer_json_path = os.path.join(
            self.s_prepare_dir,
            'connect_od_to_id.json'
        )

        self.shuttle_arcs_json_path = os.path.join(
            self.s_prepare_dir,
            'connect_arcs.json'
        )

        self.preprocessed_core_trip_json_path = os.path.join(
            self.s_prepare_dir,
            'core_trips_with_details.json'
        )

        self.preprocessed_addt_trip_json_path = os.path.join(
            self.s_prepare_dir,
            'latent_trips_with_details.json'
        )


        # stage 1 result
        self.h2h_simple_path_json_path = os.path.join(
            self.s_result_dir,
            'hub_to_hub_all_simple_path.json'
        )

        self.additional_tbd_set_json_path = os.path.join(
            self.s_result_dir,
            'stage_1_latent_tbd.json'
        )

        self.stage_1_core_trip_result_json_path = os.path.join(
            self.s_result_dir,
            'stage_1_core_result.json'
        ) 
        self.stage_1_addt_trip_result_json_path = os.path.join(
            self.s_result_dir,
            'stage_1_latent_result.json'
        )
        self.stage_1_postprocess_result_json_path = os.path.join(
            self.s_result_dir,
            'stage_1_x_elimination.json'
        )


        # stage_2 realted
        self.s_warm_start_bus_train_arcs = os.path.join(
            self.s_result_dir,
            'stage_2_warm_start_train_bus_arcs.json'
        )

        self.s_warm_start_sol = os.path.join(
            self.s_result_dir,
            'stage_2_warm_start_xyz.json'
        )

        self.s_gurobi_construct_time_json_path = os.path.join(
            self.s_result_dir,
            'stage_2_construction_time.json'
        )
        
        self.s_opt_model_path = os.path.join(
            self.s_result_dir,
            'stage_2_MIP_formulation.lp'
        )

        self.s_opt_full_sol_json_path = os.path.join(
            self.s_result_dir,
            'stage_2_full_solution.json'
        )

        self.s_opt_light_sol_json_path = os.path.join(
            self.s_result_dir,
            'stage_2_light_solution.json'
        )

        self.s_kd_design_json_path = os.path.join(
            self.s_result_dir,
            'design_solve.json'
        )

        self.s_opt_sol_mst_path = os.path.join(
            self.s_result_dir,
            'stage_2_MIP_solution.mst'
        )
        
        self.s_gurobi_log_path = os.path.join(
            self.s_result_dir,
            'stage_2_gurobi.log'
        )

    

    def _load_accessory(self):

        # Get conversion
        if self.s_time_unit_in_obj == "minute":
            self.f_time_convex_fac = 1
        elif self.s_time_unit_in_obj == 'second':
            self.f_time_convex_fac = 60
        else:
            Exception('Wrong input')

        # load pickle files & some json files
        self._load_time_dist()

        self.l_hubs = pd.read_csv(
            self.s_hub_csv_path
        )['stop_id'].tolist() # int64 to int

        self.d_demographic = du.loadJson(
            self.s_demographic_json_path
        )

    def _load_time_dist(self):

        self.d_time = du.loadPickle(
            self.s_time_min_pickle_path
        )
        self.d_dist = du.loadPickle(
            self.s_dist_km_pickle_path
        )


    def _load_preprocessed_arcs(self):

        self.l_h2h_arcs_info = du.loadJson(
            self.h2h_arcs_json_path
        )

        self.l_shuttle_arcs_info = du.loadJson(
            self.shuttle_arcs_json_path
        )

        self.d_connect_arc_name_map = du.loadJson(
            self.shuttle_arcs_refer_json_path
        )


    def _load_stage_1_alg_result(self):
        
        # load core result
        self.l_core_stage_1_res = du.loadJson(
            self.preprocessed_core_trip_json_path
        )

        self.i_num_core_ODs = len(
            [
                1
                for _ in self.l_core_stage_1_res
            ]
        )
        self.i_num_core_pax = sum(
            [
                d_trip['num_riders']
                for d_trip in self.l_core_stage_1_res
            ]
        )
       

        self.l_addt_stage_1_res = du.loadJson(
            self.stage_1_addt_trip_result_json_path
        )
        self.i_num_addt_ODs = len(
            [
                1
                for _ in self.l_addt_stage_1_res
            ]
        )
        self.i_num_addt_pax = sum(
            [
                d_trip['num_riders']
                for d_trip in self.l_addt_stage_1_res
            ]
        )


    def _load_stage_1_postprocess_result(self):

        self.d_farArcs_stage_1_res = du.loadJson(
            self.stage_1_postprocess_result_json_path
        )