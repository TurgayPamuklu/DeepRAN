"""Midhaul Module.
Creating Gurobi Class for Journal 3.

"""

from datetime import datetime
from multiprocessing import Process

from gurobipy import *  # GRB_INIT

from hcran_generic_gurobi import HcranGenericGurobi
from hcran_monitor import *
from midhaul import Midhaul

OUTPUT_PATH = "../output/"


class MidhaulGurobi(HcranGenericGurobi):  # Constants
    def __init__(self, city_name, traffic_scen, splitting_method, instance_index, day=0):
        self.midhaul_generic = Midhaul(self)
        HcranGenericGurobi.__init__(self, city_name, traffic_scen, splitting_method, instance_index, day)

    # DECISION VARIABLES
    def add_variables(self):
        self._add_variables()
        
    # CONSTRAINTS
    def add_constraints(self):
        self._add_constraints()

    def set_objective_function(self):
        power_cons_CC = self.P_CC_STA * quicksum(self.energy_prices_per_hour[t] for t in self.r_t) \
                        + self.P_CC_DU * quicksum(quicksum(self.decision_a[d][t] for d in self.r_du_in_cc) * self.energy_prices_per_hour[t] for t in self.r_t) \
                        - quicksum(self.decision_s[self.cc_index][t] * self.energy_prices_per_hour[t] for t in self.r_t) \
                        - quicksum(self.decision_p[self.cc_index][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t] for t in self.r_t)
        power_cons_EC = self.n_of_ec * self.P_EC_STA * quicksum(self.energy_prices_per_hour[t] for t in self.r_t) + self.P_EC_DU * quicksum(
            quicksum(self.decision_a[d][t] * self.energy_prices_per_hour[t] for d in range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec) for t in self.r_t) for r in self.r_ec) \
                        - quicksum(self.decision_s[r][t] * self.energy_prices_per_hour[t] for r in self.r_ec for t in self.r_t) \
                        - quicksum(self.decision_p[r][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t] for r in self.r_ec for t in self.r_t)
        self.m.setObjective(power_cons_CC + power_cons_EC)
        # self.m.setObjective(power_cons_CC + power_cons_EC)



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

        # filter_list = ["Objective Function", "DU:", "Ren:", "Total:", "Fossil:", "Batt:", "Unstored:", "Transfer:"]

        checking_delay_constraint = [[0 for x in self.r_up] for x in self.r_du]
        for d in self.r_du:
            for f in self.r_up:
                name = "decision_m_%d,%d,%d,%d" % (0, d, f, 0)
                checking_delay_constraint[d][f] = int(self.m.getVarByName(name).x)

        for d in self.r_du_in_cc:
            for f in self.r_up:
                if checking_delay_constraint[d][f] == True:
                    print("CS:: d:{} checking_delay_constraint[d][f]:{}".format(d, checking_delay_constraint[d][f]))
        r = 0
        du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
        for d in du_set_in_r:
            for f in self.r_up:
                if checking_delay_constraint[d][f] == True:
                    print("-RS:: d:{} checking_delay_constraint[d][f]:{}".format(d, checking_delay_constraint[d][f]))

        obj_val = self.midhaul_generic.calculate_the_obj_val(du_activity, solar_energy_consumption, sold_energy)
        self.rw.log_data("Objective Value:{}\n", *(obj_val,))
        self.rw.append_record_data(RecordWriter.filter_list[0], obj_val)
        self._print_variables(RecordWriter.filter_list[2], solar_energy_consumption)
        self._print_variables(RecordWriter.filter_list[3], total_consumption)
        self._print_variables(RecordWriter.filter_list[4], fossil_consumption)
        self._print_variables(RecordWriter.filter_list[5], self.remaining_battery_energy)
        self._print_variables(RecordWriter.filter_list[6], unstored_energy)
        self._print_variables(RecordWriter.filter_list[9], self.ge)
        self._print_variables(RecordWriter.filter_list[10], sold_energy)

        self.rw.log_finish()


def multi_hcran_gurobi(traffic_scen, city_name, sm):
    remaining_battery_energy = None
    print("======== traffic_scen:{} city_name:{} sm:{}".format(traffic_scen, city_name, sm))
    # for day in [1]:
    for day in range(NUMBER_OF_SIMULATION_DAY):
        instance_index = 0  # it is an extra parameter not used now
        gg = MidhaulGurobi(city_name, traffic_scen, sm, instance_index, day)  # GRB_INIT
        gg.set_initial_battery_energy(remaining_battery_energy)
        print("========  GUROBI SOLVE START:{} instance_index:{} day:{} ======== ".format(datetime.now(), instance_index, day))
        print("GUROBI SOLVE LOAD DATA:{}".format(datetime.now()))
        gg.midhaul_generic.gurobi_load_data()  # GRB_GIVEN
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
    # **************************************** CHOOSING THE METHOD ****************************************
    # STATIC -> 1 time_slot DYNAMIC -> 24 time_slot
    # NonRenewable -> self.ge[r][time_slot] = 0 Renewable -> self.ge[r][time_slot] = A real number
    # Only_CS and Only_RS means that functions are allowed to be only in one site
    splitting_methods = []
    # splitting_methods = ['NonRenewable_Static', 'NonRenewable_Dynamic', 'Renewable_Static', 'Renewable_Dynamic', 'NonRenewable_Static_OnlyCS']
    # splitting_methods = ['NonRenewable_Static', 'NonRenewable_Static_OnlyCS', 'NonRenewable_Dynamic_OnlyCS', 'NonRenewable_Static_OnlyRS', 'NonRenewable_Dynamic_OnlyRS']
    # splitting_methods = ['Renewable_Static_OnlyCS', 'Renewable_Dynamic_OnlyCS', 'Renewable_Static_OnlyRS', 'Renewable_Dynamic_OnlyRS']
    # splitting_methods = ['Renewable_Dynamic_OnlyCS']
    static_methods = ['NonRenewable_Static', 'Renewable_Static', 'NonRenewable_Static_OnlyCS',
                      'Renewable_Static_OnlyCS', 'NonRenewable_Static_OnlyRS', 'Renewable_Static_OnlyRS', ]
    standard_methods = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic']
    non_split_methods = ['TrafficAware_Renewable_Dynamic_OnlyCS', 'TrafficAware_Renewable_Dynamic_OnlyRS', 'BatteryAware_Renewable_Dynamic_OnlyCS', 'BatteryAware_Renewable_Dynamic_OnlyRS']
    clustering_methods = False
    if clustering_methods:
        use_non_split_methods = True
        use_standard_methods = True
        use_static_methods = False
        if use_non_split_methods:
            splitting_methods.extend(non_split_methods)
        if use_standard_methods:
            splitting_methods.extend(standard_methods)
        if use_static_methods:
            splitting_methods.extend(static_methods)
    else:
        # splitting_methods = ['BatteryAware_Renewable_Dynamic_OnlyRS', 'BatteryAware_Renewable_Dynamic_OnlyCS', 'BatteryAware_Renewable_Dynamic']
        # splitting_methods = ['BatteryAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic_OnlyCS']
        # splitting_methods = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic']
        splitting_methods = ['TrafficAware_Renewable_Dynamic']

    # **************************************** OPTIMIZATION  ****************************************
    multi_process = True
    if multi_process:
        for city_name in city_name_list:
            processes = []
            for traffic_scen in traffic_scenarios:
                for sm in splitting_methods:
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
            for p in processes:
                p.start()
            for p in processes:
                p.join()
        '''
        processes = []
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                for sm in splitting_methods[1]:
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        '''
    else:
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                for sm in splitting_methods:
                    print("======== traffic_scen:{} city_name:{} sm:{}".format(traffic_scen, city_name, sm))
                    multi_hcran_gurobi(traffic_scen, city_name, sm)
