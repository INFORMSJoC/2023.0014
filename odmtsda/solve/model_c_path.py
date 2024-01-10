import sys, time

from gurobipy import GRB, quicksum, LinExpr
import gurobipy
from odmtsda.utils import data_utils, other_utils
from odmtsda.solve import get_warm_start

class OptModel():

    def __init__(self, config):
        
        self.d_construct_time = {}

        self.name = 'optimization_with_adoption'
        self.model = gurobipy.Model(self.name)
        self.model.modelSense = GRB.MINIMIZE

        self._create_vars(config)
        self._add_constraints(config)
        self._save_construct_time_json(config)
        self.model.write(config.s_opt_model_path)
        print('Enhanced Model 1 is Written')

        self.model.setParam(
            "NodefileDir",
            config.s_result_dir
        )

        self.model.setParam(
            "LogFile",
            config.s_gurobi_log_path
        )

        # typical choice for gurobi
        self.model.setParam(
            "Threads",
            4
        )


    def _save_construct_time_json(self, config):

        self.d_construct_time['total_construct_time_min'] = (time.time() - self.overall_start_time) / 60
        data_utils.saveJson(
            self.d_construct_time,
            config.s_gurobi_construct_time_json_path
        )

    def _create_vars(self, config):
        
        d_warm_z = get_warm_start.run(config)
        print('======================= Warm Start Feasible Solution is Loaded')
        
        self.overall_start_time = time.time()
        start_time = time.time()

        # z each potential arc
        self.d_var_z = {}
        for d_arc in config.l_h2h_arcs_info:
            
            s_z_var_name = d_arc['arc_name']
            self.d_var_z[s_z_var_name] = self.model.addVar(
                obj = d_arc['inv_obj_beta'], 
                vtype = GRB.BINARY, 
                name = s_z_var_name
            )

            # branch and bound priority technique
            self.d_var_z[s_z_var_name].BranchPriority = 1

            if d_arc['fixed']:
                self.model.addLConstr(
                    self.d_var_z[s_z_var_name] == 1,
                    name = '{}_fixed'.format(
                        s_z_var_name
                    )
                )

            self.d_var_z[s_z_var_name].start = d_warm_z[s_z_var_name]

        # for each core trip
        self.d_var_g = {}
        self.d_var_x = {}
        self.d_var_y = {}
        for d_trip in config.l_core_stage_1_res:

            s_g_var_name = get_g_var_name(d_trip)
            self.d_var_g[s_g_var_name] = self.model.addVar(
                obj = d_trip['num_riders'],
                vtype = GRB.CONTINUOUS,
                name = s_g_var_name
            )

            for d_h2h_arc in config.l_h2h_arcs_info:
                
                # continuous x technique
                s_x_var_name = get_x_var_name(d_trip, d_h2h_arc)
                self.d_var_x[s_x_var_name] = self.model.addVar(
                    obj = 0,
                    vtype = GRB.BINARY, # GRB.CONTINUOUS, # need the number of binary var
                    ub = 1,
                    name = s_x_var_name
                )
            

            # use set: to avoid duplicate variable (when o or d is hub)
            for i_stl_arc_id in set(
                d_trip['from_orig_connect_idx'] 
                +
                d_trip['to_dest_connect_idx'] 
                +
                [d_trip['direct_connect_idx']]
            ):  
                d_stl_arc = config.l_shuttle_arcs_info[i_stl_arc_id]
                
                s_y_var_name = get_y_var_name(d_trip, d_stl_arc)
                self.d_var_y[s_y_var_name] = self.model.addVar(
                    obj = 0,
                    vtype = GRB.BINARY, # GRB.CONTINUOUS,# need the number of binary var
                    ub = 1,
                    name = s_y_var_name
                )

        
        # lambda for each additional trip each path, including direct trip
        self.f_only_adopt_add = 0
        self.d_var_lambda = {}
        self.d_var_m      = {}
        self.d_var_f      = {}
        for d_trip in config.l_addt_stage_1_res:

            if d_trip['only_reject']:
                continue
            
            if d_trip['only_adopt']:
                self.f_only_adopt_add += (
                    d_trip['num_riders']
                    *
                    (
                        d_trip['g_ub']
                        -
                        (1 - config.f_convex_theta)
                        *
                        other_utils.get_ticket_price(config)
                    )
                )              
                continue

            # define variable m
            s_m_var_name = get_m_var_name(d_trip)
            self.d_var_m[s_m_var_name] = self.model.addVar(
                obj = 0,
                vtype = GRB.CONTINUOUS,
                name = s_m_var_name
            )            
            
            for d_path in d_trip['set_Pi']:
                            
                if d_path['adopt']:
                    f_obj_fac_lambda = (
                        d_trip['num_riders']
                        *
                        (
                            d_path['g_path']
                            -
                            (1 - config.f_convex_theta)
                            *
                            other_utils.get_ticket_price(config)
                        )
                    )   
                else:
                    f_obj_fac_lambda = 0                 
                
                # define variable lambda
                s_lambda_var_name = get_lambda_var_name(d_trip, d_path)
                self.d_var_lambda[s_lambda_var_name] = self.model.addVar(
                    obj = f_obj_fac_lambda,
                    vtype = GRB.BINARY,
                    name = s_lambda_var_name
                )

                # define variable a
                s_f_var_name = get_f_var_name(d_trip, d_path)
                self.d_var_f[s_f_var_name] = self.model.addVar(
                    obj = 0,
                    vtype = GRB.BINARY,
                    name = s_f_var_name
                )

        ### add theses only-adopt to the objective function
        self.dummy_var = self.model.addVar(
            obj = self.f_only_adopt_add,
            vtype = GRB.BINARY,
            name = 'dummy_only_adopt'
        )
        self.model.addLConstr(self.dummy_var == 1, name = 'add_only_adopt')
        self.dummy_var.start = 1

        self.d_construct_time['create_vars_mins'] = (time.time() - start_time) / 60

    def _add_constraints(self, config):

        # for h2h arcs        
        self._add_cst_weak_connect(config)

        
        # cst for core trips
        self._add_cst_g(config)
        self._add_cst_x_y(config)
        self._add_cst_x_z(config)


        # cst for additional trips
        self._add_cst_z_e(config)
        self._add_cst_m_leq(config)
        self._add_cst_leq_m(config)
        self._add_cst_lambda_sum(config)


    def _add_cst_weak_connect(self, config):


        # weak connectiviy
        for i_hub_id in config.l_hubs:

            lhs = quicksum(
                self.d_var_z[d_arc['arc_name']] 
                for d_arc in config.l_h2h_arcs_info 
                if i_hub_id == d_arc['origin_stop']
            )

            rhs = quicksum(
                self.d_var_z[d_arc['arc_name']]
                for d_arc in config.l_h2h_arcs_info 
                if i_hub_id == d_arc['destination_stop']
            )
            
            s_constr_name = 'hub_{}_weak_connet'.format(i_hub_id)
            self.model.addLConstr(lhs == rhs, name = s_constr_name)
        self.model.update()

    def _add_cst_g(self, config):

        for d_trip in config.l_core_stage_1_res:
            
            s_g_var_name = get_g_var_name(d_trip)
            
            rhs_lin_1 = LinExpr(
                [
                    (
                        d_h2h_arc['rider_obj_tau'], 
                        self.d_var_x[get_x_var_name(d_trip, d_h2h_arc)] 
                    )
                    for d_h2h_arc in config.l_h2h_arcs_info
                ]
            )

            rhs_lin_2 = LinExpr(
                [
                    (
                        config.l_shuttle_arcs_info[i_stl_arc_id]['arc_obj_gamma'],
                        self.d_var_y[get_y_var_name(d_trip, config.l_shuttle_arcs_info[i_stl_arc_id])]
                    )
                    for i_stl_arc_id in set(
                        d_trip['from_orig_connect_idx'] 
                        +
                        d_trip['to_dest_connect_idx'] 
                        +
                        [d_trip['direct_connect_idx']]
                    )
                ]
            )

            self.model.addLConstr(
                self.d_var_g[s_g_var_name] == (rhs_lin_1 + rhs_lin_2),
                name = '{}'.format(
                    s_g_var_name
                )
            )

            self.model.addLConstr(
                self.d_var_g[s_g_var_name] <= (d_trip['g_ub'] + config.f_mip_numer_protect), # protect from numerical issues
                name = '{}_upper_bound'.format(
                    s_g_var_name
                )
            )

        self.model.update()

    def _add_cst_x_y(self, config):

        for d_trip in config.l_core_stage_1_res:

            i_orig = d_trip['origin_stop']
            i_dest = d_trip['destination_stop']
            l_possible_shuttle_arc = [
                config.l_shuttle_arcs_info[i_stl_idx]
                for i_stl_idx in set(
                    d_trip['from_orig_connect_idx'] 
                    +
                    d_trip['to_dest_connect_idx'] 
                    +
                    [d_trip['direct_connect_idx']]
                )
            ]

            # use set to make sure hub-origin, hub-destination, do not duplicate
            for i_stop in set([i_orig, i_dest] + config.l_hubs):

                lhs = (
                    quicksum(
                        self.d_var_y[get_y_var_name(d_trip, d_stl_arc)]
                        for d_stl_arc in l_possible_shuttle_arc
                        if d_stl_arc['origin_stop'] == i_stop
                    )
                    -
                    quicksum(
                        self.d_var_y[get_y_var_name(d_trip, d_stl_arc)]
                        for d_stl_arc in l_possible_shuttle_arc
                        if d_stl_arc['destination_stop'] == i_stop
                    )
                )


                if i_stop in config.l_hubs:
                    lhs += (
                        quicksum(
                            self.d_var_x[get_x_var_name(d_trip, d_h2h_arc)]
                            for d_h2h_arc in config.l_h2h_arcs_info
                            if (
                                d_h2h_arc['origin_stop'] == i_stop
                                and
                                (
                                    d_trip['is_core_trip']
                                    or
                                    (not config.d_farArcs_stage_1_res[d_h2h_arc['arc_name']][d_trip['trip_name']])
                                )
                            )

                        )
                        -
                        quicksum(
                            self.d_var_x[get_x_var_name(d_trip, d_h2h_arc)]
                            for d_h2h_arc in config.l_h2h_arcs_info
                            if (
                                d_h2h_arc['destination_stop'] == i_stop
                                and
                                (
                                    d_trip['is_core_trip']
                                    or
                                    (not config.d_farArcs_stage_1_res[d_h2h_arc['arc_name']][d_trip['trip_name']])
                                )
                            )

                        )
                    )
                
                else:
                    lhs += 0


                if i_stop == i_orig:
                    rhs = 1
                elif i_stop == i_dest:
                    rhs = -1
                else:
                    rhs = 0
                
                self.model.addLConstr(
                    lhs == rhs, 
                    name = '{}_stop_{}'.format(
                        d_trip['trip_name'],
                        i_stop
                    )
                )


        self.model.update()
                
            
    def _add_cst_x_z(self, config):

        
        for d_trip in config.l_core_stage_1_res:
                            
            for d_h2h_arc in config.l_h2h_arcs_info:

                s_x_var_name = get_x_var_name(d_trip, d_h2h_arc)
                s_z_var_name = d_h2h_arc['arc_name']

                
                self.model.addConstr(
                    self.d_var_x[s_x_var_name] <= self.d_var_z[s_z_var_name], 
                    name = '{}_and_{}'.format(
                        s_x_var_name,
                        s_z_var_name
                    )
                )

        self.model.update()


    
    def _add_cst_z_e(self, config):
        start_time = time.time()

        for d_trip in config.l_addt_stage_1_res:
            
            if d_trip['only_adopt'] or d_trip['only_reject']:
                continue 

            for d_path in d_trip['set_Pi']:
                
                s_f_var_name = get_f_var_name(d_trip, d_path)


                lhs = (
                    quicksum(
                        [
                            self.d_var_z[s_arc_name] 
                            for s_arc_name in d_path['arcs']
                            if s_arc_name[0] == 'z'
                        ]
                    )
                    -
                    quicksum(
                        [
                            1
                            for s_arc_name in d_path['arcs']
                            if s_arc_name[0] == 'z'
                        ]
                    )
                    +
                    1
                )
                
                
                self.model.addLConstr(
                    lhs <= self.d_var_f[s_f_var_name], 
                    name = 'z_sum_vs_{}'.format(
                        s_f_var_name
                    )
                )


                for s_arc_name in d_path['arcs']:
                    if s_arc_name[0] == 'z':
                        self.model.addLConstr(
                            self.d_var_f[s_f_var_name] <= self.d_var_z[s_arc_name], 
                            name = '{}_vs_{}'.format(
                                s_f_var_name,
                                s_arc_name
                            )
                        )    
        
        self.model.update()
    

    def _add_cst_m_leq(self, config):
        
        for d_trip in config.l_addt_stage_1_res:
            
            if d_trip['only_adopt'] or d_trip['only_reject']:
                continue 

            s_m_var_name = get_m_var_name(d_trip)
            for d_path in d_trip['set_Pi']:
                
                s_f_var_name = get_f_var_name(d_trip, d_path)
                s_lambda_var_name = get_lambda_var_name(d_trip, d_path)
                rhs = (
                    d_path['g_path']
                    +
                    config.i_big_M
                    *
                    (
                        1 - self.d_var_f[s_f_var_name]
                    )
                )
                self.model.addConstr(
                    self.d_var_m[s_m_var_name] <= rhs, 
                    name = '{}_leq_{}'.format(
                        s_m_var_name,
                        s_lambda_var_name
                    )
                )
            
        self.model.update()

    def _add_cst_leq_m(self, config):

        for d_trip in config.l_addt_stage_1_res:
            
            if d_trip['only_adopt'] or d_trip['only_reject']:
                continue

            s_m_var_name = get_m_var_name(d_trip)
            for d_path in d_trip['set_Pi']:
                
                s_lambda_var_name = get_lambda_var_name(d_trip, d_path)
                lhs = (
                    d_path['g_path']
                    -
                    config.i_big_M 
                    *
                    (
                        1 - self.d_var_lambda[s_lambda_var_name]
                    )
                )
                self.model.addConstr(
                    lhs <= self.d_var_m[s_m_var_name], 
                    name = '{}_leq_{}'.format(
                        s_lambda_var_name,
                        s_m_var_name
                    )
                )
                
        self.model.update()         
    
    def _add_cst_lambda_sum(self, config):

        for d_trip in config.l_addt_stage_1_res:
            
            if d_trip['only_adopt'] or d_trip['only_reject']:
                continue 
            
            lhs = sum(
                [
                    self.d_var_lambda[get_lambda_var_name(d_trip, d_path)]
                    for d_path in d_trip['set_Pi']
                ]
            )

            self.model.addConstr(
                lhs == 1, 
                name = '{}_lambda_sum'.format(
                    d_trip['trip_name']
                )
            )


        self.model.update()                    

    

    def solve(self):

        # self.model.setParam("OutputFlag", 0)

        solve_start_time = time.time()
        self.model.optimize()
        
        self.solve_time_sec = time.time() - solve_start_time
        self.overall_time_sec = time.time() - self.overall_start_time
    


    def gen_solution_file(self, config):

        d_all_sol = {
            'obj': self.model.ObjVal,
            'solving_time': self.solve_time_sec / config.i_second_divider,
            'overall_time': self.overall_time_sec / config.i_second_divider,
            'z': self._get_1_var_group_sol(self.d_var_z),
            'x': self._get_1_var_group_sol(self.d_var_x),
            'y': self._get_1_var_group_sol(self.d_var_y),
            'lambda': self._get_1_var_group_sol(self.d_var_lambda),
            'm': self._get_1_var_group_sol(self.d_var_m),
            'f': self._get_1_var_group_sol(self.d_var_f),
            'g': self._get_1_var_group_sol(self.d_var_g),
            'dummy': self.dummy_var.x
        }

        d_light_sol = {
            'obj': self.model.ObjVal,
            'solving_time': self.solve_time_sec / config.i_second_divider,
            'overall_time': self.overall_time_sec / config.i_second_divider,
            'z': self._get_1_var_group_sol(self.d_var_z),
            'dummy': self.dummy_var.x
        }

        data_utils.saveJson( 
            d_all_sol,
            config.s_opt_full_sol_json_path
        )

        data_utils.saveJson( 
            d_light_sol,
            config.s_opt_light_sol_json_path
        )

    def _get_1_var_group_sol(self, d_var):

        return {
            var_key : d_var[var_key].x
            for var_key in d_var.keys()
        }


# extra functions
def get_lambda_var_name(d_trip, d_adp_path):
    
    if d_adp_path['b_is_direct']:
        return (
            'lambda_{}_pi{}'.format(
                d_trip['trip_name'],
                'Direct'
            )
        )
    else:
        return (
            'lambda_{}_pi{}'.format(
                d_trip['trip_name'],
                d_adp_path['obj_rank_idx']
            )
        )


def get_f_var_name(d_trip, d_adp_path):  

    if d_adp_path['b_is_direct']:
        return (
            'f_{}_pi{}'.format(
                d_trip['trip_name'],
                'Direct'
            )
        )
    else:
        return (
            'f_{}_pi{}'.format(
                d_trip['trip_name'],
                d_adp_path['obj_rank_idx']
            )
        )

def get_x_var_name(d_trip, d_h2h_arc):
    return(
        'x_{}_{}'.format(
            d_trip['trip_name'],
            d_h2h_arc['arc_name']
        )
    )

def get_y_var_name(d_trip, d_stl_arc):
    return(
        'y_{}_{}'.format(
            d_trip['trip_name'],
            d_stl_arc['arc_name']
        )
    )

def get_m_var_name(d_trip):
    return 'm_{}'.format(d_trip['trip_name'])

def get_g_var_name(d_trip):
    return 'g_{}'.format(d_trip['trip_name'])
