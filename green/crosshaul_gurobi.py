"""Crosshaul Module.
Creating Gurobi Class for Grove Journal.

"""

from datetime import datetime
from multiprocessing import Process

from gurobipy import *  # GRB_INIT

from crosshaul import *
from hcran_generic_gurobi import HcranGenericGurobi
from hcran_monitor import *

OUTPUT_PATH = "../output/"


class CrosshaulGurobi(HcranGenericGurobi):  # Constants
    def __init__(self, city_name, traffic_scen, splitting_method, instance_index, day=0):
        if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
            self.remote_site_multiplier = instance_index
        else:
            self.remote_site_multiplier = J4_REMOTE_SITE_MULTIPLIER
        self.crosshaul_generic = Crosshaul(self)
        HcranGenericGurobi.__init__(self, city_name, traffic_scen, splitting_method, instance_index, day)
        self.traffic_converter = (1 / self.n_of_up_function)
        self.links, self.bw = self.get_link_list()
        self.node_list = []
        for u, v in self.links:
            if u not in self.node_list:
                self.node_list.append(u)
            if v not in self.node_list:
                self.node_list.append(v)

    def is_end_node_or_before_end_node(self, to_node):
        if to_node in [140, 150, 1000, self.cc_index]:
            return True
        else:
            return False

    def get_link_list(self):
        node_offset = 6
        links = tuplelist()
        bw = {}
        with open(OUTPUT_PATH + "link_list.csv", 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in csv_reader:
                if csv_reader.line_num > 1:
                    from_node = int(row[0])
                    to_node = int(row[1])
                    if to_node == 1000:
                        to_node = self.cc_index
                    bw_arc = float(row[2])
                    links.append((from_node, to_node))
                    bw[from_node, to_node] = bw_arc * self.traffic_load_multiplier
                    if self.remote_site_multiplier != 1:
                        for duplicate_no in range(1, self.remote_site_multiplier):
                            if not self.is_end_node_or_before_end_node(from_node):
                                from_node += node_offset
                                if not self.is_end_node_or_before_end_node(to_node):
                                    to_node += node_offset
                                links.append((from_node, to_node))
                                bw[from_node, to_node] = bw_arc * self.traffic_load_multiplier
        return links, bw

    # DECISION VARIABLES
    def add_variables(self):
        MAX_BANDWITH = 1000.0
        TEST_PRE_RUOTE = False
        if not TEST_PRE_RUOTE:
            self._add_variables()

        if "PreRoute" in self.splitting_method:
            self.l = [[self.links for x in self.r_t] for x in self.r_ec]
            self.z = OrderedDict()
        else:
            self.decision_l = [[0 for x in self.r_t] for x in self.r_ec]
            self.decision_z = [[0 for x in self.r_t] for x in self.r_ec]
            for t in self.r_t:
                for k in self.r_ec:
                    self.decision_l[k][t] = self.m.addVars(self.links, vtype=GRB.BINARY, name="flow")
                    self.decision_z[k][t] = self.m.addVars(self.links, lb=0.0, ub=MAX_BANDWITH, vtype=GRB.CONTINUOUS)

        if TEST_PRE_RUOTE:
            self._pre_route()
            pass

    def _pre_route(self):
        switch_ids = [110, 120, 130, 140, 150]
        bw_reducer = 6.0 / self.n_of_ec
        for t in self.r_t:
            self.l[0][t] = (0, switch_ids[0]), (switch_ids[0], switch_ids[3]), (switch_ids[3], self.cc_index)
            self.l[1][t] = (1, switch_ids[0]), (switch_ids[0], switch_ids[3]), (switch_ids[3], self.cc_index)
            self.l[2][t] = (2, switch_ids[1]), (switch_ids[1], switch_ids[3]), (switch_ids[3], self.cc_index)
            self.l[3][t] = (3, switch_ids[1]), (switch_ids[1], switch_ids[4]), (switch_ids[4], self.cc_index)
            self.l[4][t] = (4, switch_ids[2]), (switch_ids[2], switch_ids[4]), (switch_ids[4], self.cc_index)
            self.l[5][t] = (5, switch_ids[2]), (switch_ids[2], switch_ids[4]), (switch_ids[4], self.cc_index)
        k = 0
        key_is = "k:{} l:{}".format(k, (0, switch_ids[0]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[0], switch_ids[3]))
        self.z[key_is] = 15 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[3], self.cc_index))
        self.z[key_is] = 10 * self.traffic_load_multiplier * bw_reducer
        k = 1
        key_is = "k:{} l:{}".format(k, (1, switch_ids[0]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[0], switch_ids[3]))
        self.z[key_is] = 15 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[3], self.cc_index))
        self.z[key_is] = 10 * self.traffic_load_multiplier * bw_reducer
        k = 2
        key_is = "k:{} l:{}".format(k, (2, switch_ids[1]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[1], switch_ids[3]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[3], self.cc_index))
        self.z[key_is] = 10 * self.traffic_load_multiplier * bw_reducer
        k = 3
        key_is = "k:{} l:{}".format(k, (3, switch_ids[1]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[1], switch_ids[4]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[4], self.cc_index))
        self.z[key_is] = 10 * self.traffic_load_multiplier * bw_reducer
        k = 4
        key_is = "k:{} l:{}".format(k, (4, switch_ids[2]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[2], switch_ids[4]))
        self.z[key_is] = 15 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[4], self.cc_index))
        self.z[key_is] = 10 * self.traffic_load_multiplier * bw_reducer
        k = 5
        key_is = "k:{} l:{}".format(k, (5, switch_ids[2]))
        self.z[key_is] = 30 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[2], switch_ids[4]))
        self.z[key_is] = 15 * self.traffic_load_multiplier
        key_is = "k:{} l:{}".format(k, (switch_ids[4], self.cc_index))
        self.z[key_is] = 10 * self.traffic_load_multiplier * bw_reducer

        node_offset = 6
        for duplicate_no in range(1, self.remote_site_multiplier):
            for t in self.r_t:
                for pre_links in range(0, node_offset):
                    link_order = 0
                    link_list_tuple = []
                    for link in self.l[pre_links][t]:
                        if not self.is_end_node_or_before_end_node(link[0]):
                            from_node = link[0] + node_offset * duplicate_no
                        else:
                            from_node = link[0]
                        if not self.is_end_node_or_before_end_node(link[1]):
                            to_node = link[1] + node_offset * duplicate_no
                        else:
                            to_node = link[1]
                        link_list_tuple.append((from_node, to_node))
                        if link_order == 2:
                            self.l[pre_links + node_offset * duplicate_no][t] = link_list_tuple[0], link_list_tuple[1], link_list_tuple[2]

                        old_key_is = "k:{} l:{}".format(pre_links, (link[0], link[1]))
                        new_key_is = "k:{} l:{}".format(pre_links + node_offset * duplicate_no, (from_node, to_node))
                        self.z[new_key_is] = self.z[old_key_is]
                        link_order += 1

    # CONSTRAINTS
    def add_constraints(self):
        BIG_M = 1e5
        self._add_constraints()

        if "PreRoute" in self.splitting_method:
            self._pre_route()
        else:
            for t in self.r_t:
                for u in self.node_list:
                    for k in self.r_ec:
                        self.m.addConstr(quicksum(self.decision_l[k][t][u, v] for u, v in self.links.select(u, '*'))
                                         - quicksum(self.decision_l[k][t][v, u] for v, u in self.links.select('*', u)) ==
                                         (1 if u == k else -1 if u == self.cc_index else 0), 'node%s_' % u)
        for t in self.r_t:
            ORIGINAL_BW_CONSTRAINT = False
            if ORIGINAL_BW_CONSTRAINT:
                for u, v in self.links:
                    self.m.addConstr(quicksum(self.decision_l[k][t][u, v] *
                                              quicksum(self.traffic_load[i][t] * self.traffic_converter * self.decision_m[i][d][f][t]
                                                       for f in self.r_up
                                                       for d in list(self.r_du_in_cc)
                                                       for i in list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec)))
                                              for k in self.r_ec)
                                     <= self.bw[u, v])
            elif "PreRoute" in self.splitting_method:
                for k in self.r_ec:
                    for link_index in range(3):
                        link_name = self.l[k][t][link_index]
                        key_is = "k:{} l:{}".format(k, link_name)
                        self.m.addConstr(quicksum(self.traffic_load[i][t] * self.traffic_converter * self.decision_m[i][d][f][t]
                                                  for f in self.r_up
                                                  for d in list(self.r_du_in_cc)
                                                  for i in list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec)))
                                         <= self.z[key_is])
            else:
                for u, v in self.links:
                    for k in self.r_ec:
                        self.m.addConstr(quicksum(self.traffic_load[i][t] * self.traffic_converter * self.decision_m[i][d][f][t]
                                                  for f in self.r_up
                                                  for d in list(self.r_du_in_cc)
                                                  for i in list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec)))
                                         <= BIG_M * (1 - self.decision_l[k][t][u, v]) + self.decision_z[k][t][u, v])
                    self.m.addConstr(quicksum(self.decision_z[k][t][u, v] for k in self.r_ec) <= self.bw[u, v])

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

    # def _print_route(self):
    #     self.rw.log_data("------- BW -----------\n")
    #     # for t in self.r_t:
    #     for t in range(9, 10, 1):
    #         for u, v in self.links:
    #             bw_usage = sum(self.decision_l[k][t][u, v].x *
    #                            sum(self.traffic_load[i][t] * self.traffic_converter * self.decision_m[i][d][f][t].x for f in self.r_up
    #                                for d in list(self.r_du_in_cc)
    #                                for i in list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec)))
    #                            for k in self.r_ec)
    #             self.rw.log_data("t:{} u,v:{} bw usage:{} bw cap:{}\n", *(t, (u, v), bw_usage, self.bw[u, v]), )
    #             print_z = []
    #             for k in self.r_ec:
    #                 if self.decision_l[k][t][u, v].x == 0:
    #                     print_z.append(-1)
    #                 else:
    #                     print_z.append(self.decision_z[k][t][u, v].x)
    #             self.rw.log_data("bw dedicated:{}\n", *(print_z,))
    #
    #         self.rw.log_data("------- LINKS -----------\n")
    #         for k in self.r_ec:
    #             for i, j in self.links:
    #                 if (self.decision_l[k][t][i, j].x > 0):
    #                     self.rw.log_data("Route:{} {} {} {} {}\n", *(t, k, i, j, self.decision_l[k][t][i, j].x))

    def print_variables(self):
        self.init_the_record_writer()
        self._print_general_info()
        # if not "PreRoute" in self.splitting_method:
        #     self._print_route()
        traffic_load = [[0 for x in self.r_t] for x in self.r_cloud]
        for t in self.r_t:
            for k in self.r_ec:
                user_in_ec = range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec)
                for i in user_in_ec:
                    traffic_load[k][t] += self.traffic_load[i][t]
        self._print_variables("Traffic:", traffic_load)
        # mg = MonitorTraffic()
        # mg.plt_traffic_in_a_day_period(traffic_load)

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

        # self.plot_network()
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

        obj_val = self.crosshaul_generic.calculate_the_obj_val(du_activity, solar_energy_consumption, sold_energy)
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


def multi_hcran_gurobi(traffic_scen, city_name, sm, day):
    CREATE_TRAFFIC_DATA = False
    PLOT_NETWORKX = False
    if PLOT_NETWORKX:
        cg1 = CrosshaulGurobi(city_name, traffic_scen, sm, 1, 0)
        cg2 = CrosshaulGurobi(city_name, traffic_scen, sm, 2, 0)
        cg4 = CrosshaulGurobi(city_name, traffic_scen, sm, 4, 0)
        nG = NetworkGraph(cg1, cg2, cg4)
        nG.plot_network()
        exit(0)
    if CREATE_TRAFFIC_DATA:
        for ts in traffic_scenarios:
            print("Creating Data for ts rate {} and {} days...".format(ts, NUMBER_OF_SIMULATION_DAY))
            gg = CrosshaulGurobi("istanbul", ts, sm, 4, 0)
            gg.crosshaul_generic.create_traffic()
        print("Process is finished successfully")
        exit(0)
    remaining_battery_energy = None
    print("======== traffic_scen:{} city_name:{} sm:{}".format(traffic_scen, city_name, sm))
    if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
        instance_index_list = [4, 2, 1]
    elif SOLAR_PANEL_SIZE_AS_A_MULTIPLIER:
        instance_index_list = [0.25, 0.5, 1, 2, 4]
    elif DU_CAPACITY_SIZE_AS_A_MULTIPLIER:
        instance_index_list = [1, 2, 4, 8, 16]
    else:
        instance_index_list = [0]
    for instance_index in instance_index_list:
        gg = CrosshaulGurobi(city_name, traffic_scen, sm, instance_index, day)  # GRB_INIT
        gg.set_initial_battery_energy(remaining_battery_energy)
        print("========  GUROBI SOLVE START:{} instance_index:{} day:{} ======== ".format(datetime.now(), instance_index, day))
        print("GUROBI SOLVE LOAD DATA:{}".format(datetime.now()))
        gg.crosshaul_generic.load_data()  # GRB_GIVEN
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


SOLAR_PANEL_PRICE = 2000  # per kWh
BATTERY_PRICE = 0.15  # per Wh


def cap_exp_calculator():
    instance_index_list = [0.25, 0.5, 1, 2, 4]
    for ins in instance_index_list:
        gg = CrosshaulGurobi("istanbul", 1, "BatteryAware_Renewable_Dynamic", ins, 0)
        cap_ex = 0
        for ec in gg.r_ec:
            cap_ex += gg.solar_panel_size[ec] * SOLAR_PANEL_PRICE + gg.battery_capacity[ec] * BATTERY_PRICE
            # print(cap_ex)
        cap_ex += gg.solar_panel_size[gg.cc_index] * SOLAR_PANEL_PRICE + gg.battery_capacity[gg.cc_index] * BATTERY_PRICE
        # print(cap_ex)
        # cap_ex = int(cap_ex * 0.25)
        print("{} size:{} Total CapEx:{}".format(ins, gg.solar_panel_size, cap_ex))

if __name__ == '__main__':
    CAP_EXP_CALC = False
    if CAP_EXP_CALC:
        cap_exp_calculator()
        exit()
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
        splitting_methods = ['BatteryAware_Renewable_Dynamic']
        #  splitting_methods = ['BatteryAware_Renewable_Dynamic', 'TrafficAware_Renewable_Dynamic']
        # splitting_methods = ['BatteryAware_Renewable_Dynamic_PreRoute']
        # splitting_methods = ['BatteryAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic_PreRoute', 'TrafficAware_Renewable_Dynamic']

    # **************************************** OPTIMIZATION  ****************************************
    multi_process = True
    if multi_process:
        SELECT_METHOD = False
        RUN_CITIES_SEPARATED = False
        if SELECT_METHOD:
            processes = []
            for city_name in city_name_list:
                if city_name is 'stockholm':
                    for traffic_scen in traffic_scenarios:
                        for sm in splitting_methods:
                            for day in range(NUMBER_OF_SIMULATION_DAY):
                                processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm, day)))
                elif city_name is 'istanbul':
                    traffic_scen = 3
                    sm = 'BatteryAware_Renewable_Dynamic_PreRoute'
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
                elif city_name is 'jakarta':
                    traffic_scen = 3
                    sm = 'BatteryAware_Renewable_Dynamic'
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
                    sm = 'TrafficAware_Renewable_Dynamic'
                    processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
            for p in processes:
                p.start()
            for p in processes:
                p.join()
        elif RUN_CITIES_SEPARATED:
            for city_name in city_name_list:
                processes = []
                for traffic_scen in traffic_scenarios:
                    for sm in splitting_methods:
                        processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm)))
                for p in processes:
                    p.start()
                for p in processes:
                    p.join()
        else:
            processes = []
            for city_name in city_name_list:
                for traffic_scen in traffic_scenarios:
                    for sm in splitting_methods:
                        for day in range(NUMBER_OF_SIMULATION_DAY):
                            processes.append(Process(target=multi_hcran_gurobi, args=(traffic_scen, city_name, sm, day)))
            for p in processes:
                p.start()
            for p in processes:
                p.join()
    else:
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                for sm in splitting_methods:
                    print("======== traffic_scen:{} city_name:{} sm:{}".format(traffic_scen, city_name, sm))
                    multi_hcran_gurobi(traffic_scen, city_name, sm, 7)
