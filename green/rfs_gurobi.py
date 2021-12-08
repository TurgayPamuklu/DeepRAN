"""Rfs Module.
Uncompleted/Cancelled RFS Journal Implementation (Journal 2).

"""

from datetime import datetime
from multiprocessing import Process

SWITCH_ON_OPTIMIZATION = True
if SWITCH_ON_OPTIMIZATION:
    from gurobipy import *  # GRB_INIT

from rfs import RenFuncSplit
from hcran_monitor import *

from rfs_analog import RfsAnalog

OUTPUT_PATH = "../output/"
from hcran_generic_gurobi import HcranGenericGurobi


class rfsGurobi(HcranGenericGurobi, RenFuncSplit):  # CONSTANTS
    def __init__(self, city_name, traffic_scen, splitting_method, instance_index, day=0):
        HcranGenericGurobi.__init__(self, city_name, traffic_scen, splitting_method, instance_index, day)

    # DECISION VARIABLES
    def add_variables(self):
        self.__add_variables()

        if not SWITCH_ON_OPTIMIZATION:
            for t in self.r_t:
                for i in self.r_i:
                    print("tl:{} res:{} self.INV_UPSILON:{}".format(self.traffic_load[i][t], self.traffic_load[i][t] * self.INV_UPSILON, self.INV_UPSILON))

        for t in self.r_t:
            for j in self.r_j:  # cell activity decision. j%self.n_of_sc_per_ec=0 is macro cell and we does not use them. Test it!
                self.decision_g[j][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_g_%d,%d" % (j, t))
        for t in self.r_t:
            for j in self.r_j:  # cell CRF operation decision. j%self.n_of_sc_per_ec=0 is macro cell and we does not use them. Test it!
                self.decision_h[j][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_h_%d,%d" % (j, t))
        for t in self.r_t:
            for j in self.r_j:  # cell assignment decision.
                for i in self.r_i:
                    self.decision_z[i][j][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_z_%d,%d,%d" % (i, j, t))

    # CONSTRAINTS
    def add_constraints(self):
        BIG_M = 1e5
        self.__add_constraints()

        # ANALOG PART CONSTRAINTS (J3:11-15)#############################
        cell_set_size = 5
        for t in self.r_t:
            for k in self.r_k:
                user_set_in_k = list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec))
                cell_set_in_k = list(range(k * self.n_of_cell_per_ec, (k + 1) * self.n_of_cell_per_ec))
                small_cell_set_in_k = list(range(k * self.n_of_cell_per_ec + 1, (k + 1) * self.n_of_cell_per_ec))
                for i in user_set_in_k:
                    self.m.addConstr(quicksum((1 / self.rfs_nsr[i][j % cell_set_size][t]) * self.decision_z[i][j][t] for j in cell_set_in_k) >= 1)  # J3:11
                    self.m.addConstr(quicksum(self.decision_z[i][j][t] for j in cell_set_in_k) == 1)  # J3:12
                for j in cell_set_in_k:
                    self.m.addConstr(quicksum(self.rfs_nsr[i][j % cell_set_size][t] * self.decision_z[i][j][t] for i in user_set_in_k) <= self.RHO)  # J3:13
                for j in small_cell_set_in_k:
                    if "SwitchOn" in self.splitting_method:
                        self.m.addConstr(self.decision_g[j][t] == 1)  # J3:14
                    else:
                        self.m.addConstr(BIG_M * self.decision_g[j][t] - quicksum(self.decision_z[i][j][t] for i in user_set_in_k) >= 0)  # J3:14
                    self.m.addConstr(self.decision_g[j][t] - self.decision_h[j][t] >= 0)  # J3:15

    def set_objective_function(self):
        power_cons_CC = self.P_CC_STA * quicksum(self.energy_prices_per_hour[t] for t in self.r_t) \
                        + self.P_CC_DU * quicksum(quicksum(self.decision_a[d][t] for d in self.r_du_in_cc) * self.energy_prices_per_hour[t] for t in self.r_t) \
                        - quicksum(self.decision_s[self.cc_index][t] * self.energy_prices_per_hour[t] for t in self.r_t) \
                        - quicksum(self.decision_p[self.cc_index][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t] for t in self.r_t)
        power_cons_EC = self.n_of_ec * self.P_EC_STA * quicksum(self.energy_prices_per_hour[t] for t in self.r_t) + self.P_EC_DU * quicksum(
            quicksum(self.decision_a[d][t] * self.energy_prices_per_hour[t] for d in range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec) for t in self.r_t) for r in self.r_ec) \
                        - quicksum(self.decision_s[r][t] * self.energy_prices_per_hour[t] for r in self.r_ec for t in self.r_t) \
                        - quicksum(self.decision_p[r][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t] for r in self.r_ec for t in self.r_t)
        power_cons_SC = quicksum(self.decision_g[j][t] * self.P_SC_ANALOG + self.decision_h[j][t] * self.P_SC_BB for j in self.r_j for t in self.r_t)
        self.m.setObjective(power_cons_CC + power_cons_EC + power_cons_SC)
        # self.m.setObjective(power_cons_CC + power_cons_EC)

        '''
        self.m.setObjective(self.P_CC_STA * quicksum(self.energy_prices_per_hour[t] for t in self.r_t)
                            + self.P_CC_DU * quicksum(self.decision_a[d][t] * self.energy_prices_per_hour[t] for d in self.r_du_in_cc for t in self.r_t)
                            - quicksum(self.decision_s[self.cc_index][t] * self.energy_prices_per_hour[t] for t in self.r_t)
                            - quicksum(self.decision_p[self.cc_index][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t] for t in self.r_t)
                            + self.n_of_ec * self.P_EC_STA * quicksum(self.energy_prices_per_hour[t] for t in self.r_t)
                            + self.P_EC_DU * quicksum(
            quicksum(self.decision_a[d][t] * self.energy_prices_per_hour[t] for d in range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec) for t in self.r_t) for r in self.r_ec)
                            - quicksum(self.decision_s[r][t] * self.energy_prices_per_hour[t] for r in self.r_ec for t in self.r_t)
                            - quicksum(self.decision_p[r][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t] for r in self.r_ec for t in self.r_t)
                            + quicksum(self.decision_g[j][t] * self.P_SC_ANALOG + self.decision_h[j][t] * self.P_SC_BB for j in self.r_j for t in self.r_t)
                            , GRB.MINIMIZE)
        '''


    def solve_the_problem(self):
        self.m.optimize()

    def print_variables(self):
        self.init_the_record_writer()
        self._print_general_info()

        if self.m.status == GRB.Status.INF_OR_UNBD:
            self.rw.log_data("Model is infeasible or unbounded\n", None)
            self.rw.log_finish()
            return
        if self.m.status == GRB.Status.INFEASIBLE:
            self.rw.log_data("Model is Infeasible\n", None)
            self.rw.log_finish()
            return
        if self.m.status == GRB.Status.INFEASIBLE:
            self.rw.log_data("Model is Unbounded\n", None)
            self.rw.log_finish()
            return

        self.rw.log_data("Objective Value From Solver:{}\n", *(self.m.objVal,))

        self.rw.log_data("MIPGap:{}\n", *(self.m.MIPGap,))
        self.rw.append_record_data("MIPGap", self.m.MIPGap)

        ########################################################################################################
        # Getting DECISION VARIABLES
        du_activity = [[0 for x in self.r_t] for x in self.r_du]  # decision_a
        for d in self.r_du:
            for t in self.r_t:
                name = "decision_a_%d,%d" % (d, t)
                du_activity[d][t] = int(self.m.getVarByName(name).x)

        number_of_active_du_per_site, total_number_of_active_du_cs, total_number_of_active_du_rs = self.calculate_number_of_active_du_per_site(du_activity)
        self._print_total_number_of_active_du(total_number_of_active_du_cs, total_number_of_active_du_rs)
        self._print_variables(RecordWriter.filter_list[1], number_of_active_du_per_site)

        if self.ENERGY_TRANSFER_AVAILABLE:
            energy_transfer_matrix = [[[0 for x in self.r_t] for x in self.r_cloud] for x in self.r_cloud]
            for t in self.r_t:
                for i in self.r_cloud:
                    for j in self.r_cloud:
                        name = "decision_x_%d,%d,%d" % (i, j, t)
                        v = self.m.getVarByName(name)
                        energy_transfer_matrix[i][j][t] += int(v.x)
            self._print_variables_3(RecordWriter.filter_list[7], energy_transfer_matrix)

        total_consumption = self.calculate_total_consumption(number_of_active_du_per_site)

        solar_energy_consumption = [[0 for x in self.r_t] for x in self.r_cloud]  # decision_s
        sold_energy = [[0 for x in self.r_t] for x in self.r_cloud]  # decision_p
        fossil_consumption = [[0 for x in self.r_t] for x in self.r_cloud]
        unstored_energy = [[0 for x in self.r_t] for x in self.r_cloud]  # it will be sold in a reduced money in Traffic Aware Method

        if 'TrafficAware' in self.splitting_method or 'Static' in self.splitting_method:
            for t in self.r_t:
                for r in self.r_cloud:
                    if t == 0:
                        amount_of_solar_energy = int(self.initial_battery_energy[r] + self.ge[r][t])
                    else:
                        amount_of_solar_energy = int(self.remaining_battery_energy[r][t - 1] + self.ge[r][t])
                    if total_consumption[r][t] - amount_of_solar_energy > 0:
                        solar_energy_consumption[r][t] = amount_of_solar_energy
                        fossil_consumption[r][t] = total_consumption[r][t] - amount_of_solar_energy
                    else:
                        fossil_consumption[r][t] = 0
                        solar_energy_consumption[r][t] = total_consumption[r][t]
                        if amount_of_solar_energy - solar_energy_consumption[r][t] > self.battery_capacity[r]:
                            unstored_energy[r][t] = amount_of_solar_energy - solar_energy_consumption[r][t] - self.battery_capacity[r]
                            self.remaining_battery_energy[r][t] = self.battery_capacity[r]
                        else:
                            unstored_energy[r][t] = 0
                            self.remaining_battery_energy[r][t] = amount_of_solar_energy - solar_energy_consumption[r][t]
            for r in self.r_cloud:
                for t in self.r_t:
                    sold_energy[r][t] = unstored_energy[r][t]

        if 'BatteryAware' in self.splitting_method:
            for r in self.r_cloud:
                for t in self.r_t:
                    name = "decision_be_%d,%d" % (r, t)
                    self.remaining_battery_energy[r][t] = int(self.m.getVarByName(name).x)
                    name = "decision_s_%d,%d" % (r, t)
                    solar_energy_consumption[r][t] = int(self.m.getVarByName(name).x)
                    name = "decision_p_%d,%d" % (r, t)
                    sold_energy[r][t] = int(self.m.getVarByName(name).x)
                    fossil_consumption[r][t] = total_consumption[r][t] - solar_energy_consumption[r][t]
                    if fossil_consumption[r][t] < 0:
                        fossil_consumption[r][t] = 0
                    if t == 0:
                        remaining_battery_energy_before_consumption = self.initial_battery_energy[r]
                    else:
                        remaining_battery_energy_before_consumption = self.remaining_battery_energy[r][t - 1]
                    energy_in_an_unlimited_battery = remaining_battery_energy_before_consumption + self.ge[r][t] - solar_energy_consumption[r][t] - sold_energy[r][t]
                    if energy_in_an_unlimited_battery > self.battery_capacity[r]:
                        unstored_energy[r][t] = energy_in_an_unlimited_battery - self.battery_capacity[r]
                    else:
                        unstored_energy[r][t] = 0

            for t in range(0, self.n_of_time_slot):
                for r in self.r_cloud:
                    unstored_energy[r][t] = int(self.remaining_battery_energy[r][t - 1] + self.ge[r][t] - self.battery_capacity[r])
                    if unstored_energy[r][t] < 0:
                        unstored_energy[r][t] = 0

        print_dec_g = [[0 for x in self.r_t] for x in self.r_j]
        print_dec_h = [[0 for x in self.r_t] for x in self.r_j]
        for t in self.r_t:
            for k in self.r_k:
                cell_set_in_k = list(range(k * self.n_of_cell_per_ec, (k + 1) * self.n_of_cell_per_ec))
                for j in cell_set_in_k:
                    name = "decision_g_%d,%d" % (j, t)
                    print_dec_g[j][t] = int(self.m.getVarByName(name).x)
                    name = "decision_h_%d,%d" % (j, t)
                    print_dec_h[j][t] = int(self.m.getVarByName(name).x)
        # filter_list = ["Objective Function", "DU:", "Ren:", "Total:", "Fossil:", "Batt:", "Unstored:", "Transfer:"]

        decision_z = [[[0 for x in self.r_t] for x in self.r_j] for x in self.r_i]  # ijt
        bs_assigned_user = [[0 for x in self.r_t] for x in self.r_j]
        for t in self.r_t:
            for j in self.r_j:
                for i in self.r_i:
                    name = "decision_z_%d,%d,%d" % (i, j, t)
                    decision_z[i][j][t] = int(self.m.getVarByName(name).x)
                    bs_load = self.rfs_nsr[i][j % 5][t] * decision_z[i][j][t]

                    # if decision_z[i][j][t] == 1:
                    #     print("i:{} j:{} t:{} rfs_nsr:{} decision_z:{} bs_load:{}".format(i, j, t, self.rfs_nsr[i][j % 5][t], decision_z[i][j][t], bs_load ))

                    bs_assigned_user[j][t] += decision_z[i][j][t]

        # ---------------------- BEGIN: DEBUG PURPOSE
        max_min_delay = []
        max_min_delay_wo_NOF = []
        print_decision_m = [[[[0 for x in self.r_t] for x in self.r_up] for x in self.r_du] for x in self.r_i]  # idft
        for t in self.r_t:
            for i in self.r_i:
                number_of_urf_in_cc = 0
                number_of_urf_in_ec = 0
                for d in self.r_du_in_cc:
                    for f in self.r_up:
                        name = "decision_m_%d,%d,%d,%d" % (i, d, f, t)
                        print_decision_m[i][d][f][t] = int(self.m.getVarByName(name).x)
                        number_of_urf_in_cc += print_decision_m[i][d][f][t]
                ec_no = self._get_cloud_from_user(i)
                du_set_in_k = list(range(ec_no * self.n_of_du_per_ec, (ec_no + 1) * self.n_of_du_per_ec))
                for d in du_set_in_k:
                    for f in self.r_up:
                        name = "decision_m_%d,%d,%d,%d" % (i, d, f, t)
                        print_decision_m[i][d][f][t] = int(self.m.getVarByName(name).x)
                        number_of_urf_in_ec += print_decision_m[i][d][f][t]

                D_FROM_SC = self.D_MWAVE * 1
                D_PROCESS = self.traffic_load[i][t] * self.DU_GOPS_PERF * self.SMALL_OMEGA
                D_RSF = self.traffic_load[i][t] * self.D_RSF_TRSF * self.D_RSF_NRSF
                D_NOF = self.D_NOF_TOF * self.D_NOF_CONS * 10E3 * sum(print_decision_m[i][d][f][t] for f in self.r_up for d in self.r_du_in_cc)
                print_Delay_wo_NOF = self.D_CONS_FROM_EC + D_FROM_SC + D_PROCESS + D_RSF
                print_Delay = self.D_CONS_FROM_EC + D_FROM_SC + D_PROCESS + D_RSF + D_NOF
                max_min_delay.append(print_Delay)
                max_min_delay_wo_NOF.append(print_Delay_wo_NOF)
                '''
                print("t:{} i:{} # URF in CC:{} in EC:{} D_NOF:{} print_Delay_wo_NOF:{} Delay:{} delay_threshold:{} traffic:{} "
                      .format(t,i,number_of_urf_in_cc, number_of_urf_in_ec, D_NOF, print_Delay_wo_NOF, print_Delay, self.delay_threshold[i][t], self.traffic_load[i][t]))
                '''
        print("Delay Max:{} Min:{}".format(max(max_min_delay), min(max_min_delay)))
        print("max_min_delay_wo_NOF Max:{} Min:{}".format(max(max_min_delay_wo_NOF), min(max_min_delay_wo_NOF)))
        print("delay_threshold Max:{} Min:{}".format(max(self.delay_threshold), min(self.delay_threshold)))
        # ------------------------ END: DEBUG

        obj_val = self.calculate_the_obj_val(du_activity, solar_energy_consumption, sold_energy, print_dec_g, print_dec_h)
        self.rw.log_data("Objective Value:{}\n", *(obj_val,))
        self.rw.append_record_data(RecordWriter.filter_list[0], obj_val)
        self._print_variables(RecordWriter.filter_list[2], solar_energy_consumption)
        self._print_variables(RecordWriter.filter_list[3], total_consumption)
        self._print_variables(RecordWriter.filter_list[4], fossil_consumption)
        self._print_variables(RecordWriter.filter_list[5], self.remaining_battery_energy)
        self._print_variables(RecordWriter.filter_list[6], unstored_energy)
        self._print_variables(RecordWriter.filter_list[9], self.ge)
        self._print_variables(RecordWriter.filter_list[10], sold_energy)
        self._print_variables_cells(RecordWriter.filter_list[11], print_dec_g)
        self._print_variables_cells(RecordWriter.filter_list[12], print_dec_h)
        self._print_variables_cells(RecordWriter.filter_list[13], bs_assigned_user)

        self.rw.log_finish()


def multi_hcran_gurobi(traffic_scen, city_name, sm):
    remaining_battery_energy = None
    print("======== datetime:{} traffic_scen:{} city_name:{} sm:{}".format(datetime.now(), traffic_scen, city_name, sm))
    for day in [1]:
        # for day in range(NUMBER_OF_SIMULATION_DAY):
        instance_index = 0  # it is an extra parameter not used now
        gg = rfsGurobi(city_name, traffic_scen, sm, instance_index, day)  # GRB_INIT
        gg.set_initial_battery_energy(remaining_battery_energy)
        print("========  GUROBI SOLVE START:{} instance_index:{} day:{} ======== ".format(datetime.now(), instance_index, day))
        print("GUROBI SOLVE LOAD DATA:{}".format(datetime.now()))
        gg.load_data()  # GRB_GIVEN
        print("GUROBI SOLVE add_variables:{}".format(datetime.now()))
        gg.add_variables()  # GRB_DECISION
        print("GUROBI SOLVE add_constraints:{}".format(datetime.now()))
        gg.add_constraints()  # GRB_CONSTRAINTS
        print("GUROBI SOLVE set_objective_function:{}".format(datetime.now()))
        gg.set_objective_function()  # GRB_OBJ
        print("GUROBI SOLVE solve_the_problem:{}".format(datetime.now()))
        gg.solve_the_problem()  # GRB_RUN
        print("GUROBI SOLVE END:{}".format(datetime.now()))
        gg.print_variables()  # GRB_RSLT
        if NUMBER_OF_SIMULATION_DAY is not 1:  # we add this line for get rid of an error in static methods
            remaining_battery_energy = gg.get_remaining_battery_energy()


if __name__ == '__main__':
    # splitting_methods = ["BatteryAware_Renewable_Dynamic"]
    splitting_methods = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic', 'BatteryAware_SwitchOn_Dynamic']
    CREATE_TRAFFIC_DATA = False
    if CREATE_TRAFFIC_DATA:
        for ts in traffic_scenarios:
            print("Creating Data for ts rate {} and {} days...".format(ts, NUMBER_OF_SIMULATION_DAY))
            gg = rfsGurobi("istanbul", ts, "Heuristic_Renewable", 0)
            gg.create_traffic()
            rfs = RfsAnalog(gg.n_of_cell_per_ec, gg.n_of_ec, gg.number_of_ue_per_ec, ts)
            rfs.create_rfs_nsr()

        print("RFS NSR and Traffic is created successfully.")
        # exit(0)

    # **************************************** OPTIMIZATION  ****************************************
    multi_process = True
    if multi_process:
        '''
        processes = []
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                for sm in splitting_methods:
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        '''
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                processes = []
                for sm in splitting_methods:
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
                for p in processes:
                    p.start()
                for p in processes:
                    p.join()

    else:
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                for sm in splitting_methods:
                    print("======== traffic_scen:{} city_name:{} sm:{}".format(traffic_scen, city_name, sm))
                    multi_hcran_gurobi(traffic_scen, city_name, sm)
